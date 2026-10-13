"""Read running project image identities and OS package manifests. No pulls or secret environment dumps."""
import datetime
import hashlib
import json
import subprocess
import uuid

from poc_control import ROOT, compose, docker_env


def main():
    env = docker_env()
    services = [json.loads(line) for line in compose("ps", "--format", "json", capture=True).stdout.splitlines()]
    images, service_refs, packages, relations = {}, [], [], []

    def docker(*args):
        return subprocess.run(["docker", *args], env=env, capture_output=True, text=True, check=True, timeout=60).stdout

    for service in services:
        container = service["ID"]
        image_id = docker("inspect", "--format", "{{.Image}}", container).strip()
        service_refs.append({"service": service["Service"], "image_id": image_id})
        if image_id in images:
            continue
        try:
            metadata = json.loads(docker("image", "inspect", image_id))[0]
            image_metadata_available = True
        except subprocess.CalledProcessError:
            # A running container may refer to an image no longer retained by the engine.
            metadata = {"Os": "linux", "Architecture": docker("exec", container, "uname", "-m").strip(), "RepoDigests": []}
            image_metadata_available = False
        image_ref = "SPDXRef-Image-" + str(len(images)+1)
        packages.append({"name": "project-container-image", "SPDXID": image_ref, "downloadLocation": "NOASSERTION",
                         "filesAnalyzed": False, "licenseConcluded": "NOASSERTION", "licenseDeclared": "NOASSERTION",
                         "copyrightText": "NOASSERTION", "checksums": [{"algorithm": "SHA256", "checksumValue": image_id.split(":", 1)[1]}],
                         "comment": "Image identity only; local image ID is not a registry distribution digest."})
        relations.append({"spdxElementId": "SPDXRef-DOCUMENT", "relationshipType": "DESCRIBES", "relatedSpdxElement": image_ref})
        # Capture only package names/versions/architecture, never full container inspection/environment.
        detected = docker("exec", container, "sh", "-c", "command -v dpkg-query || command -v apk || true").strip()
        rows, manager = [], "UNAVAILABLE"
        if detected.endswith("dpkg-query"):
            manager = "dpkg"
            output = docker("exec", container, "dpkg-query", "-W", "-f=${Package}\t${Version}\t${Architecture}\n")
            rows = [line.split("\t") for line in output.splitlines() if len(line.split("\t")) == 3]
        elif detected.endswith("apk"):
            manager = "apk"
            # The installed database is the authoritative package record, not repository latest versions.
            output = docker("exec", container, "cat", "/lib/apk/db/installed")
            for block in output.split("\n\n"):
                fields = dict(line.split(":", 1) for line in block.splitlines() if ":" in line)
                if fields.get("P") and fields.get("V"):
                    rows.append([fields["P"], fields["V"], fields.get("A", "NOASSERTION")])
        for index, (name, version, architecture) in enumerate(rows):
            reference = image_ref + "-Package-" + str(index+1)
            packages.append({"name": name, "SPDXID": reference, "versionInfo": version, "downloadLocation": "NOASSERTION",
                             "filesAnalyzed": False, "licenseConcluded": "NOASSERTION", "licenseDeclared": "NOASSERTION",
                             "copyrightText": "NOASSERTION", "comment": "Installed OS package; architecture="+architecture})
            relations.append({"spdxElementId": image_ref, "relationshipType": "CONTAINS", "relatedSpdxElement": reference})
        images[image_id] = {"image_id": image_id, "repo_digests": metadata.get("RepoDigests", []),
                            "os": metadata["Os"], "architecture": metadata["Architecture"],
                            "engine_image_metadata_available": image_metadata_available,
                            "package_manager": manager, "os_package_count": len(rows), "spdx_ref": image_ref}
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    document = {"spdxVersion": "SPDX-2.3", "dataLicense": "CC0-1.0", "SPDXID": "SPDXRef-DOCUMENT",
                "name": "media-trace-development-installed-images", "documentNamespace": "https://spdx.org/spdxdocs/media-trace-"+str(uuid.uuid4()),
                "creationInfo": {"creators": ["Tool: media-trace-installed-package-collector-1"], "created": now},
                "packages": packages, "relationships": relations,
                "comment": "Observed image and installed OS package inventory; unmanaged binaries, Python, npm, model weights and license conclusions require separate sources. Not a vulnerability scan or release approval."}
    path = ROOT/"docs/00-project/validation/image-sbom.spdx.json"
    path.write_text(json.dumps(document, indent=2)+"\n")
    report = {"status": "PASS", "scope": "read_only_project_images_and_installed_OS_package_inventory_collection",
              "observed_at": now, "services": service_refs, "images": list(images.values()),
              "sbom_path": path.relative_to(ROOT).as_posix(), "sbom_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
              "spdx_packages": len(packages), "all_dependency_inventory_complete": False,
              "vulnerability_scan_executed": False, "licenses_reviewed_or_release_approved": False,
              "production_frozen": False, "services_restarted": False,
              "unmanaged_binaries_and_redistribution_notices_pending": True}
    (ROOT/"docs/00-project/validation/stage-two-software-report.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"status": "PASS", "services": len(services), "images": len(images), "spdx_packages": len(packages)}))


if __name__ == "__main__":
    main()
