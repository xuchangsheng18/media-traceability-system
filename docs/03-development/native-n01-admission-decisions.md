# N01剩余准入事项与确认清单

2026-10-18（北京时间）。本页统一记录当前剩余工作和需要确认的事项，不再通过不断新增材料轮次代替实际风险处置。**N01仍未通过整体准入；Python候选继续暂缓，原100包锁和共享服务保持。**

[机器确认清单](../00-project/validation/native-n01-admission-decisions/confirmation-register.json) · [12条CVE逐项状态](../00-project/validation/native-n01-admission-decisions/python-pg-open-items.json) · [游标具体修复申请](native-n01-cursor-hardening-change-request.md) · [原生状态](native-linux-execution-status.json) · [任务导航](../../tasks/README.md)


## 当前核验：无新增上游答复，原计划与导航已校准

截至2026-10-18 23:36:16（北京时间），两处issue均为open；eastasianwidth共1条评论，agent共2条评论，均没有晚于本项目询问的新评论。两条已发正文仍与批准原稿逐字节一致；[当前查询及先前观察](../00-project/validation/native-n01-admission-decisions/upstream-contact-status.json)保留时间、完整分页计数和评论标识，未再次发送消息。

本批不依赖回复的工作已完成：[原N01五项计划对账](native-linux-implementation-plan.md#n01五项计划的实际状态)、[Linux实际重验](../00-project/validation/native-n01-admission-decisions/n01-plan-verification.json)。45项现有工具测试0失败/错误/跳过；10类原始制品校验通过；前后10个项目容器ID和31个相邻容器集合相同。修正原计划末尾早期“32项/3包”的当前状态及包校验PASS含义，精简T004当前显示说明并保留证据和原170任务字段。历史首次RED运行记录本批未验证，不编造；不因此新增准入阻塞。

**现在无需你重复确认或操作。** 已授权询问和八项限定认可均已落实。仍缺两项发布者精确版本依据、Python维护与9条记录的正式处置、必要软件准入及最终安装锁；Python候选继续暂缓。缺少具体新材料时不请求笼统“同意全部风险”。N02账号/目录、N03服务、N04公钥/业务恢复、N07切换保留在各自阶段；当前没有可执行的管理员安装或停写命令。

## 当前决定：八项限定复核已认可，两处上游询问已发送

用户已明确授权按两份原草稿联系上游，并认可PostgreSQL、RabbitMQ、OTP、SeaweedFS、Keycloak、Java、Nginx、age在同一单位内部研发范围的限定技术复核。[实际认可记录](../00-project/validation/native-n01-admission-decisions/eight-component-limited-review-decision.json)绑定审阅提交`2801e72`、当时待决表的Git字节摘要、八项精确恢复归档及三份重建二进制；不将对话认可冒充身份独立验真或数字签名。

八项状态已更新为`ACCEPTED_LIMITED_INTERNAL_TECHNICAL_REVIEW`。**这不是正式软件/全部许可兼容准入，不允许安装，也不是N01整体通过。** Python和Node不在这八项中；Python候选继续暂缓，原100包锁及现有服务不变。D10无需重复确认。

### 两项上游联系已完成发送

用户完成浏览器登录后，执行方已按原稿在两处现有issue各发布一条评论；未新建重复issue、未更换询问版本。GitHub接口回读确认作者`xuchangsheng18`、目标issue、正文与批准原稿第一处空行后的内容**逐字节相同**。初次连接器403及登录交接作为历史尝试保留，后续浏览器成功不抹去失败证据。

| 精确版本 | 已发送并核对的评论 | 页面凭证 |
| --- | --- | --- |
| eastasianwidth0.2.0 | [issue18评论6251444294](https://github.com/komagata/eastasianwidth/issues/18#issuecomment-6251444294) | [截图](../00-project/validation/native-n01-admission-decisions/upstream-eastasianwidth-comment.png) |
| @npmcli/agent3.0.0 | [issue176评论6251454639](https://github.com/npm/agent/issues/176#issuecomment-6251454639) | [截图](../00-project/validation/native-n01-admission-decisions/upstream-agent-comment.png) |

[机器发送回执](../00-project/validation/native-n01-admission-decisions/upstream-contact-status.json)保存评论ID、时间、原稿与实际正文摘要、初次403、用户完成登录及后续成功结果。原草稿Target/Status头仍作为当时的历史元数据，不是当前发送状态，也没有被发送给上游。原草稿可继续用于核对，不需再发送一次。

**D09的发送授权与执行、D10的八项限定认可均已落实，目前无需用户重复确认或操作。** 当前是`SENT_VERIFIED_AWAITING_PUBLISHER_REPLY`；我们自己的询问不是发布者原通知或许可答复，两个通知缺口关闭数仍为0。

N01尚缺：两项精确版本通知/适用范围的发布者依据、Python维护与9条记录的正式处置、剩余必要的软件准入及最终安装锁。上游收到询问也不能直接算通知已取得；后续须核对答复者身份、精确版本与正文范围后更新。N02/N04/N07安装、公钥及切换依原前置另行执行。

## 先前核验：精确版本通知与同主体内部范围

用户已明确答复“仅同一单位或公司内部使用”，见[原话与边界记录](../00-project/validation/native-n01-admission-decisions/same-entity-internal-use-decision.json)。这只明确运行包当前使用范围；GitHub源码和资料仍然公开。未来向其他独立单位、外包主体复制运行包、改变组件、修改字体或启动未选插件时重新复核；不能把内部范围当成可以删除现有版权和通知的授权。

| 精确版本 | 本轮取得及核验 | 尚缺的适用范围依据 |
| --- | --- | --- |
| `eastasianwidth 0.2.0`，gitHead `b89f04d44dc786885615e94cd6e2ba1ef7866fa4` | 找到官方`1d41951`提交新增的MIT正文，原版权行是`Copyright komagata`、没有年份；正文通过Git blob摘要核对并[原样保留为后来版本参考](../02-architecture/third-party-notices/eastasianwidth-later-0.3.0-MIT-LICENSE.reference.txt)。 | 加入许可证时package.json为0.3.0；与0.2.0之间主JS有190行变更，不是相同字节。尚无维护者确认该正文覆盖0.2.0及README所致谢的改编代码/数据；不能填造年份或把后来版本静默替换。 |
| `@npmcli/agent 3.0.0`，gitHead `94f346d882458ac9481d015c55057d15f5899bf1` | 保留精确包/源码ISC声明；补查官方常规许可文件历史及现有issue。 | issue176主题为4.0.0；其中询问3.0.0的是普通参与者，不是发布者确认。仍缺适用于3.0.0的完整版权/许可通知，或明确覆盖该版本的官方汇总通知。 |

[逐版本证据](../00-project/validation/native-n01-admission-decisions/publisher-notice-version-scope-review.json)保留官方提交、比较、GitHub报告的签名状态和观察范围。GitHub标记verified不冒充本地独立验签；后来的真实通知已取得1份，但两个精确版本的缺口关闭数仍为0。现有他人提问不代表本项目已联系上游或已获授权。

### 逐软件准入的具体进展

本轮在Linux重新读取保留附录中的793条材料绑定：Node430、JDK244、RabbitMQ107、OTP10、Nginx1及PG1。各条字节/大小匹配，见[实际检查](../00-project/validation/native-n01-admission-decisions/software-primary-material-byte-check.json)。这是六组已保留材料的重验，不是重新扫描全部运行库、全部兼容性裁决或新制品采用。

[十软件逐项待决表](../00-project/validation/native-n01-admission-decisions/component-scoped-admission-proposal.json)现在绑定每项精确恢复归档、重建二进制、已有材料、内部使用条件和后续阶段。Python因维护/9条记录、Node因两项通知仍阻塞；另外八项的限定技术复核现已获用户认可，见上方实际决定；软件正式准入决定仍为空。既有服务功能、数据库/对象恢复、公钥和切换分别仍由N03/N04/N07验收，不倒置成N01资料必须伪造的运行结果。

### 原D09/D10请求（已获授权/认可，保留请求范围）

1. **D09，上游联系。** [eastasianwidth草稿](../00-project/validation/native-n01-admission-decisions/eastasianwidth-publisher-inquiry.draft.txt)和[agent草稿](../00-project/validation/native-n01-admission-decisions/npmcli-agent-publisher-inquiry.draft.txt)已准备，目标分别是现有issue18和issue176。已获明确授权按原草稿各发一条；实际执行结果见上方状态，不新建重复issue、不披露本项目部署或作商业承诺。需要的是发布者对精确版本的原通知/范围答复，不是重复回答“暂无”。
2. **D10，徐昌胜逐项复核。** 用户已认可上述八项限定技术复核，不再重复请求。不是要求批准未知风险、全部许可兼容、安装或N01整体通过；Python和Node不在这八项中。

Python候选仍暂缓，不重复要求维护证明；本轮没有管理员命令、安装、业务迁移或服务切换。待真实通知/技术处置及必要准入决定齐备后再生成最终安装锁，N01当前仍未整体完成。

## 本轮可独立完成项：依赖边界与运行库许可来源

[41处解码边界](../00-project/validation/native-n01-admission-decisions/decoder-boundary-review.json) · [12项内存观察](../00-project/validation/native-n01-admission-decisions/dependency-boundary-probes.json) · [消息契约5项及失效对照](../00-project/validation/native-n01-admission-decisions/message-boundary-regression-proof.json) · [临时目录观察](../00-project/validation/native-n01-admission-decisions/temp-permission-observations.json) · [89OS/25Conda材料](../00-project/validation/native-n01-admission-decisions/runtime-package-notice-review.json) · [104库来源与许可材料关联](../00-project/validation/native-n01-admission-decisions/library-provider-notice-review.json)。原[9条逐项处置](../00-project/validation/native-n01-admission-decisions/nine-cve-disposition-review.json)继续保留，正式关闭数仍为0；不再把已完成的来源盘点说成未采集。

41处依赖解码按常量、SDK响应/分页、消息、Schema/编码类型、可选会话/HTTPBasic、构建工具、文件系统、Torch编译/分布式等实际边界逐项记录。4处URL-safe语法位置中，Pydantic的3.15分支在当前3.10不执行，因此仅3处是当前解释器的分支候选；这仍不是实际可达性或全部启用的证明。

12项内存观察确认Pydantic、wheel、Kombu及SDK分页/校验头仍接受部分编码别名，未修补这些库。Botocore拒绝错误内容摘要、项目图片入口拒绝填充后尾部；dateutil实际转发固定资源。上传工作者经真实Kombu解码后，4类bytes/额外字段事件在授权与SQL之前被既有契约拒绝，普通JSON对照到达自有授权哨兵即停止；没有访问数据库、消息队列或完成业务操作。新增[5项回归测试](../../tests/business/test_upload_json_boundary.py)已通过；在独立进程故意停用Schema校验时4项按预期失败、正常实现恢复为5项通过，生产代码未修改。仅JSON序列化配置不能代替事件类型与权限校验。

当前默认临时根和私有父目录中，两次新建空目录均为0700；16处项目TemporaryDirectory位于验证/工具代码，42处依赖调用也包括测试、构建与可选运行功能。没有执行符号链接竞态、改TMPDIR或改现有ACL；目录创建模式不能替代未来服务账号和不可信并发写入验证。

本轮从精确归档补齐89个OS包的版权材料，包括跨包文档链接；25个Conda包中20个在info部分有正文、2个在pkg部分实际带有info/licenses，另3个libgcc/libgomp/libsqlite按已验证归档中的精确构建配方取得GCC16.2.0和SQLite3.53.4源码条款。三者仍不是“Conda随包正文已找到”，也没有声称Conda二进制与源码逐字节等价或全部对应源码/构建条件完整。GCC的例外与SQLite库正文不自动覆盖所有构建脚本和第三方。

13份公共条款文本已与GPG验证的Ubuntu索引所列base-files13ubuntu10归档逐字节匹配。该包仅为许可参考来源，不安装、不采用，不替换宿主已观察的13ubuntu10.4，也不写进运行版本锁。

104份既有解析库已重新核对摘要并关联：26个OS直接库、6个OS私有副本、18个Conda库、43个wheel成员、8个JDK库及3个PostgreSQL私有库。43成员来自numpy/Pillow/psycopg-binary/Torch的精确wheel，已与归档字节匹配；JDK关联既有法律材料集合，不冒充逐原生子组件兼容性批准。GNU readline历史链接用户为Python扩展与psql，不把它的条款自动赋给全部PG服务器或整个应用。新私有附录保留210条材料关联、130个不同摘要；数量是材料绑定，不是许可证数量或准入分数。

### 前一批材料检查时的确认状态（当前以D09/D10为准）

- **此前材料批次无需新增确认或管理员操作。** Python候选继续暂缓；不重复询问暂无的维护证明或两项发布者通知。
- `eastasianwidth`0.2.0与`@npmcli/agent`3.0.0的精确通知仍未取得，D08已记录“暂无”；上游联系请求未发送，不用其他作者、年份或模板填造通知。以后取得发布者原文时再提供路径/官方链接。
- 逐软件正式准入须在具体技术处置、许可兼容及使用范围具备证据后由徐昌胜作决定；当前不请求“全部同意”。本轮材料来源已补齐的部分不再重复采集；仍未关闭的9条记录、维护风险和两项通知继续保留。
- N02管理员安装、N04公钥及停写切换仍是后续步骤；此次不运行安装包、不修改现有版本锁或服务，不增加170任务整卡验收数。

最新CI绑定具体源码提交和上传制品摘要，见[CI机器报告](../00-project/validation/github-actions-report.json)。新增5项测试须随本轮源码实际运行，不沿用前轮241项结果冒充本轮。

## 本轮九条漏洞、发布者通知与逐软件复核

[9条逐项处置](../00-project/validation/native-n01-admission-decisions/nine-cve-disposition-review.json) · [精确上游记录](../00-project/validation/native-n01-admission-decisions/nine-cve-authoritative-source-refresh.json) · [依赖调用清单](../00-project/validation/native-n01-admission-decisions/dependency-callsite-inventory.json) · [实际探测与D02专项](../00-project/validation/native-n01-admission-decisions/disposition-runtime-checks.json) · [两包发布者通知核查](../00-project/validation/native-n01-admission-decisions/two-publisher-notice-review.json) · [十类软件逐项复核](../00-project/validation/native-n01-admission-decisions/component-admission-review.json)。以下为当前状态；后续章节保留此前来源与观察。

本轮静态清单覆盖124个项目Python文件、8597个已安装Python源文件，其中22/170个含目标候选文本的文件完成AST分析，无解析错误。依赖中发现41处Base64解码（37处标准字母表、4处URL-safe）、42处TemporaryDirectory及1处pkgutil.get_data调用；项目有16处TemporaryDirectory和2处解码。未观察到已解析的IMAP、POP、parseaddr及js_output直接调用。这是按文件导入别名的候选清单，不覆盖完整数据流、动态/编译代码或未来插件，不能写成全路径不可达。

| CVE | 本轮完成的实际处置/核查 | 仍未关闭的内容 |
| --- | --- | --- |
| CVE-2023-36632 | 上游保留争议。当前parseaddr为(addr, *, strict=True)，已保留前后校验源码；124项目文件和8597已安装Python源文件候选扫描无直接parseaddr调用。不能把严格参数当递归/输入上限的全面修复。 | 未证明第三方间接邮件解析及超长输入全路径；启用邮件解析时明确长度上限、异常处理与有界测试，正式处置待复核。 |
| CVE-2025-12781 | D02两处游标统一严格编码入口，21项专项重跑通过。解释器仍接收标准字母表别名；已安装依赖41处解码中4处URL-safe调用分别在Pydantic和两份wheel实现。 | Pydantic Base64URL类型和wheel恢复/安装输入需逐路径核对；不得把D02推广为所有第三方解码已修复。 |
| CVE-2025-15366 | 当前项目及已安装Python源候选AST扫描无已解析imaplib调用；旧内存命令观察仍保留，不伪造模块修补。 | 启用IMAP、插件或间接调度前，须补受维护修补或经批准的命令控制字符拒绝及相应测试；现有扫描不足以关闭整解释器记录。 |
| CVE-2025-15367 | 当前项目及已安装Python源候选AST扫描无已解析poplib调用；旧内存命令观察仍保留。 | 启用POP/插件前须补受维护修补或经批准的控制字符拒绝及测试；不修改库或把未观察到调用当全环境不可达。 |
| CVE-2026-12003 | 上游描述为VPATH回退及父目录权限条件；现有只读VPATH/父目录/ACL观察保留，当前并非已验收的高权限服务环境。 | 不创建landmark或实施目录攻击；N02落实不可由低权限主体改写的服务代码和祖先目录，N03以实际账号验证，当前不签整环境不受影响。 |
| CVE-2026-12345 | 16处项目与42处已安装依赖TemporaryDirectory直接调用已列出；rmtree防符号链接标记不覆盖上游所述全部文件标志风险。 | 后续获准实现私有临时根、非特权运行和写入主体限制，并按最终账号验证；本轮仅清单，不改变TMPDIR/ACL/清理逻辑，不登记已修复。 |
| CVE-2026-3446 | D02专项21项通过；无害探测确认默认解码忽略填充后尾部、validate=True拒绝该输入。依赖41处解码中，仅2处标准字母表调用显式validate=True，37处标准/4处URL-safe分别保留上下文。 | 按各调用的真实协议/信任边界核对；尤其S3响应校验、消息序列化、会话中间件和Pydantic类型。是否需要代码变更按具体申请处理，不直接修改第三方或降低断言。 |
| CVE-2026-3479 | 上游明确get_data按open安全模型并保留争议；唯一已解析依赖调用为dateutil.zoneinfo，包名__name__和资源常量dateutil-zoneinfo.tar.gz已记录源码。项目无直接调用。 | 该固定调用未观察到外部resource参数；不证明动态loader或变量重绑定绝无风险。未来接受外部资源路径时必须授权、约束和测试，不将争议当全软件准入。 |
| CVE-2026-6019 | 合成cookie探测仍出现字面</script>序列，未在浏览器执行。当前项目/已安装Python源候选扫描无已解析js_output调用。 | 不能将不可信cookie拼入内联脚本；启用该API前补修补或改用安全响应头路径并验证，不把零匹配当解释器已修复。 |

6项无害行为观察保留实际值；其中默认Base64接收尾部、Morsel输出脚本闭合序列是风险仍在的证据，不能称安全测试通过。D02的21项专项实际通过；它限定于两处业务游标。首次辅助探测错误预期parseaddr没有strict参数，已保留[失败观察](../00-project/validation/native-n01-admission-decisions/disposition-runtime-checks.initial.json)，随后读取实际源码确认strict=True及前后校验，纠正的是探测预期，并未修改解释器或证明递归类问题全面修复。

两包已重新获取精确npm发布归档并验证registry SHA512，与gitHead源码逐文件对照：eastasianwidth0.2.0的3文件、@npmcli/agent3.0.0的8文件全部一致。[实际制品复核](../00-project/validation/native-n01-admission-decisions/disposition-materials-verification.json)另确认：预选Node归档中的9个JS/package.json文件均匹配；2份README未随Node包提供，不将发布包11文件全部说成已嵌入Node。8721份Python源文件摘要已在Linux重核，19份本轮来源材料已私有归档、逐项重读校验。完整源码归档分别5/43个普通文件，全文检查仍只见MIT/ISC元数据声明，没有取得发布者版权/许可通知。author元数据不等于可代填版权通知；本轮发布者通知关闭数为0。Node目标实际捆绑npm10.9.9，早期辅助下载的npm10.9.4 LICENSE不作为该精确目标的依据。

需要补充材料时，徐昌胜可向两个上游提供下列**尚未发送**的核验请求；本轮没有向外发消息，也不要求批准未知风险：

- [eastasianwidth上游](https://github.com/komagata/eastasianwidth)：请求确认0.2.0／b89f04d44dc786885615e94cd6e2ba1ef7866fa4适用的MIT全文、实际版权通知和年份（若上游原本没有年份，不补造），并提供可保存的发布者链接或原文。
- [@npmcli/agent上游](https://github.com/npm/agent)：请求确认3.0.0／94f346d882458ac9481d015c55057d15f5899bf1适用的ISC全文与实际版权通知。需要保留回复出处、时间、原文摘要及适用版本，不能用其他版本许可自动覆盖本版本。

如果已有这些权威材料，只需提供本地文件或官方链接。没有时，保持这两项材料待补；排除npm/更换制品属于新的具体变更，当前未实施。无需管理员安装、发密码/Token或重复确认Python暂缓。

十类软件均已按精确制品及已有材料展开当前使用、通知保留、第三方边界和各自剩余事项；没有把Node的MIT、JDK的Classpath例外或项目Apache-2.0覆盖所有依赖。当前仅团队内部研发，也不凭该表述认定所有成员属同一法律主体；将来运行包交付的接收者/源码路径需按实际范围核对。Python维护/9条记录与两包通知尚未关闭；其他组件的材料复核不是正式准入决定。所有formal_decision继续为空，installation_permitted=false，最终安装锁、N02/N03服务验收和N04业务数据恢复尚未执行。

本轮未增加170任务整卡验收数，Python候选继续暂缓，原100包锁及现有服务不变。最新CI以[机器报告](../00-project/validation/github-actions-report.json)所绑定的源码提交、制品摘要和实际测试结果为准，随后回执提交只包含忽略路径，不倒填为重新跑过代码门禁。

## 当前恢复组合与Go缓存核验

[恢复组合评审稿](../../config/native/recovery-combination.review.json)将10个组件、96份wheel、25个Conda包、89个OS恢复包、40个构建包及已认可的3项预选逐一关联，原制品锁和原100包版本锁保留。旧Node及原age/Seaweed二进制留作历史来源，不与新预选混用。该文件是恢复输入评审稿，不能作为安装许可或最终采用锁。

首次全量Go声明图检查发现917条缺件结果（916个不同模块/版本）；原缓存支持既定目标不代表全量声明图齐备。针对精确缺件已补取1242个文件请求，Go按既有锁及校验数据库认证；补充恢复校验值与预选锁分开。完整声明图中的外部模块/版本恢复记录为age 17个模块、seaweedfs 1159个模块。随后关闭Go模块与工具链联网，从新缓存执行7项核验；3个目标使用原预选go.mod/go.sum只读构建，产物摘要均与预选一致。不能把补充校验值写成采用了新依赖版本。

[Go恢复归档核验](../00-project/validation/native-n01-admission-decisions/go-cache-archive-restore-report.json)记录5077个恢复输入文件；归档逐文件核对后解到空目录，重新完成两个完整模块图的离线下载和verify。另有1项有效输入对照及缺件、损坏2项拒绝检查。这里的离线仅指Go代理/校验服务和工具链下载已关闭，不声称采用了操作系统网络隔离；选定模块图也不表示每个模块都链接进运行二进制。[初次失败](../00-project/validation/native-n01-admission-decisions/go-recovery-report.initial.json)保留。

[许可附录](../00-project/validation/native-n01-admission-decisions/recovery-license-appendix-report.json)有794条材料关联、440个不同摘要，其中479条为许可/法律声明候选材料，315条为包/应用元数据；包括预选Node的430个目标文件、tzdata的2份许可、JDK的244条法律材料关联，以及RabbitMQ/OTP/nginx的目标材料。82个RabbitMQ应用与[当前4启用、2显式插件](../00-project/validation/native-n01-admission-decisions/rabbitmq-active-scope.json)已匹配。原485文件资料包摘要未变；不同材料包存在重复，不将计数相加当独立许可总数。eastasianwidth0.2.0与@npmcli/agent3.0.0的发布者通知及整体逐软件准入仍未关闭。

本轮关闭的是选定恢复输入、Go缓存及材料关联的技术缺口。N01整体仍受Python维护/其余9条漏洞及软件准入阻塞，Python候选继续暂缓。N03原生运行、N04数据库/对象/队列恢复属于后续任务，不能冒充本轮已完成，也不倒置为N01前置。当前没有新增需要用户重复确认或立即管理员安装的事项。

## 本轮恢复来源纠正与许可参考材料

本轮查明：Python的`tzdata 2026.5`由pip安装，Conda的`tzdata 2026c`归档只有系统时区数据，不包含Python发行包。原100包版本锁本来就要求`tzdata==2026.5`，本次补取相同版本wheel，632个文件与现有安装一致，并留存2份随包许可材料；没有升级、重新安装或创建Python候选。恢复获取清单现为**96份wheel＋4个由Conda负责的Python发行包**。历史95份wheel获取事实保留，原“五包均由Conda覆盖”的推断被本次证据纠正，不能把2026c与2026.5当作版本别名。

[纠正证据](../00-project/validation/native-n01-admission-decisions/tzdata-recovery-correction.json)、[来源观察](../00-project/validation/native-n01-admission-decisions/tzdata-origin-observation.json)与[初次不完整结果](../00-project/validation/native-n01-admission-decisions/recovery-input-crosswalk.initial.json)保留完整关系。[限定输入交叉核对](../00-project/validation/native-n01-admission-decisions/recovery-input-crosswalk.json)覆盖10主要包、96wheel、25Conda、89OS恢复包及4候选输入：共224记录、223个不同摘要；100个当前Python发行包名称/版本映射一致，40构建包的精确摘要全部包含于89恢复包集合。它不是完整prefix文件核验、最终安装锁、全部Go缓存或实际恢复通过。

Node剩余两包的MIT/ISC[标准条款参考材料](../00-project/validation/native-n01-admission-decisions/node-license-reference-materials.json)已留存来源和摘要。标准文本不能冒充精确发布者通知；不填造版权年份、权利人，也不将ISC示例版权归给`@npmcli/agent`。两包通知及实际使用义务仍列为未完成。当前限定为团队内部研发，不自动授权运行包外发。

N01仍为`IN_PROGRESS_BLOCKED_ADMISSION`：R1暂无Python维护证明且候选暂缓；R2原12条中3条限定结论已认可，其余9条继续处置；R3逐软件准入、R4最终组合、R5服务账号与可选路径、R6最终安装锁均保留。当前无需重复确认已作出的决定，管理员安装、迁移、正式备份和切换尚未执行。

## CI核验与修复前历史观察

本轮开始时已核验的前轮源码提交`25c4dec6a1292061a956edbcc72687aed6a1d751`的[CI39119876583](https://github.com/xuchangsheng18/media-traceability-system/actions/runs/39119876583)成功：241项业务测试、32项门禁及6份关键报告通过；330510字节制品SHA256为`55061728b14a84adcc127083ef2805950fe634dceab27abffeaea6bd424e36da`。本轮Go恢复更新提交按自己的CI记录，不将此前通过倒填。

D02修复前（源码`ba99b743`）在既有Linux py310中完成[11项解析观察](../00-project/validation/native-n01-admission-decisions/cursor-parser-observations.json)，直接调用当时的解析函数、使用自有内存数据库协作者，未连接真实数据库或网络，未运行HTTP/RLS验收，不能把夹具返回当业务实现通过。

修复前的控制分页接受同一已签名原始游标的跨字母表编码别名；夹具中记录范围不变，载荷和调用者变更被HMAC拒绝。上传分页先校验编码文本HMAC，拒绝未重新签名的文本变更，但未强制规范编码；持有合成测试签名密钥的夹具签发方仍可生成被接收的非规范文本。没有据此认定发生无密钥伪造或越权。该历史记录不修改或冒充修复后结果；本轮已由[D02验证回执](../00-project/validation/d02-cursor-hardening-report.json)证明这两处应用入口的拒绝行为。

现有默认解码行为仍可观察到填充后内容被忽略。[Python官方版本表](https://devguide.python.org/versions/)本次仍列3.10为2026-10-01停止支持；[本次上游记录核对](../00-project/validation/native-n01-admission-decisions/upstream-review.json)说明相关兼容性补丁不等于立即严格拒绝其他字母表。应用约束与解释器维护是两个事项，不能互相替代。

## 本次补齐与当前未完成内容

[逐项剩余工作](../00-project/validation/native-n01-admission-decisions/current-work-items.json) · [调用与权限事实](../00-project/validation/native-n01-admission-decisions/current-runtime-and-callsite-facts.json) · [Node预选包材料](../00-project/validation/native-n01-admission-decisions/node-preselection-bundled-materials.json) · [7个精确包回溯](../00-project/validation/native-n01-admission-decisions/node-preselection-license-fallback.json)

本轮实际核对124个项目Python文件的36个相关调用和7个动态属性访问点；未发现所列邮件解析、IMAP/POP、pkgutil.get_data、Morsel.js_output的直接调用，7个动态点为日志/错误元数据或固定推理属性名，不是这些API的已观察调度。此结论不覆盖第三方依赖、完整数据流、编译模块或未来插件，不能写成全项目不可达。

Linux只读权限检查显示：VPATH的Modules/setup.local当前不存在，/home受当前模式及ACL保护；当前研发prefix归研发账号控制，部分目录组可写，外层也有0700目录。不能仅据单个775就认定任意用户可写，也不能将研发账号可写环境直接当作更高权限服务的可信运行目录。/tmp为1777，私有项目运行目录为0700。实际专用账号、最终临时目录及依赖并发写入仍须N02/N03核验；本轮不改/opt、不运行目录攻击。[PSF的VPATH记录](https://raw.githubusercontent.com/CVEProject/cvelistV5/main/cves/2026/12xxx/CVE-2026-12003.json)和[TemporaryDirectory记录](https://raw.githubusercontent.com/CVEProject/cvelistV5/main/cves/2026/12xxx/CVE-2026-12345.json)不支持凭rmtree标志或一次目录观察直接宣称漏洞已修复。

Node22.23.3实际二进制匹配已确认预选摘要；197处许可材料（99种摘要）、197条具名包记录（186组名称/版本）和36个仅声明模块类型的元数据已关联。36个标记不是36个未许可组件。7个无包根独立许可文件的具名包另按精确发布版本、官方registry摘要及可用文本回溯；没有独立LICENSE不自动等于无许可，也不把声明/README自动当成全部许可义务完成。233份包元数据与197处许可材料共430个目标文件已逐一匹配验真后的预选归档（零差异）；不是整包所有成员或全部许可适用性的证明。旧Node22.21.1清单不代替此新包。具体npm、BlueOak、CC-BY等随附声明以原材料为准，不套用Node本体MIT覆盖。

| 剩余项 | 还未完成的具体工作 | 责任与顺序 |
| --- | --- | --- |
| R1 维护依据 | Python3.10延长维护/补丁覆盖证明已确认暂无；候选继续暂缓 | 以后取得新材料时再验证；当前保留未完成，不重复索要、不自动接受风险 |
| R2 12条CVE处置 | D02完成；3条当前目标限定不适用技术结论已获徐昌胜认可，另9条保留实际调用、补丁或条件处置事项 | 执行方逐项补证，徐昌胜复核具体结论，不能一并签为安全 |
| R3 十类软件准入 | 精确制品、必要功能、随附许可/通知与已知扫描尚未形成逐组件实际准入决定 | 已有嵌套材料和三项预选保持有效；不重复收集已齐材料，不用空白审批替代技术处置 |
| R4 最终恢复组合 | 96wheel＋4Conda发行包、25Conda/89OS及Go恢复输入组合和缓存归档重放已核；最终安装采用待软件准入 | N03服务运行/N04业务数据恢复另行验收，不要求制作整个宿主镜像 |
| R5 账号与能力边界 | 当前用户的权限观察不是未来专用账号运行验证；必要功能与可选功能须区分 | N01明确边界；N02落实账号，N03实测。FIPS/HSM/LDAP/Kerberos/GPU等未选能力启用前另验，不倒置阶段依赖 |
| R6 安装锁 | 最终可安装锁未生成；原锁保留，三项候选仅预选 | 必需准入条件具备后由执行方生成和验证；当前不安装 |


对7包的进一步复核：imurmurhash0.1.4的完整MIT正文在精确README中；@sigstore/verify2.1.1关联到registry所记源码提交的根Apache正文，但不据此宣称整个包代码与源码逐字节相同。eastasianwidth0.2.0和@npmcli/agent3.0.0的精确发布README未带正文，所查完整源码树也无独立许可命名文件，保留MIT/ISC声明与材料待核状态，不伪造版权。spdx-exceptions、spdx-license-ids与err-code的声明、引用和实际文本分别保留，许可ID数据中的许可证名称不作为包自身许可结论。此处仍有真实材料/义务复核工作，不能仅靠“认可全部”关闭。

### 本轮答复已登记：当前无需重复确认

徐昌胜已明确回复“暂无证明，继续保留待处置状态”和“认可三项限定技术结论”。[决定记录](../00-project/validation/native-n01-admission-decisions/user-bounded-review-decision.json)绑定已审阅的`c41578f`文档摘要；这是对话确认记录，不是数字签名。

- Python3.10暂无维护/补丁证明已确认，R1继续待处置，3.13/3.12候选继续暂缓；不把此答复登记为风险接受，不重复要求相同信息。
- CVE-2017-8806、CVE-2024-3220、CVE-2026-3298仅针对当前Linux/py310及已观察私有PG产品集合的限定不适用技术结论已获认可。原扫描及历史技术状态保留，产品/平台/API或部署范围变化重新核验。
- 其余9条记录、Python生命周期风险和十类软件整体准入未获一并认可；D02已完成，但不代表CPython已修补。

本轮没有新的管理员操作或重复确认要求。后续只有出现新的证明材料、具体技术变更或已准备好的准入决定时再提示。N02安装包、N04正式age公钥及停写/切换仍按前置条件执行；徐昌胜保管备份且公钥尚未建立的记录不变。

### 十类软件分别还缺什么（R3展开）

| 软件与精确目标 | 已有材料不重做 | 仍需完成的准入内容 |
| --- | --- | --- |
| Python3.10.22 | 原100包锁、来源归档、D02及限定漏洞检查 | 维护/补丁依据、逐CVE实际处置；不能以版本可运行代替维护支持 |
| Node22.23.3预选（原锁22.21.1） | 预选摘要、扫描/前端验证、本轮197声明和材料 | 精确新包随附许可/署名与实际使用义务复核、最终采用决定；不是重问预选 |
| PostgreSQL16.15 | 源包/构建、依赖及postgresql-common不在当前目标的观察 | 限定漏洞结论复核、实际依赖/许可与最终精确组合核对；N03/N04功能/恢复另验 |
| RabbitMQ4.3.6 | 官方归档、随附正文盘点和依赖输入 | 明确实际OTP/所需插件组合与随附义务，完成其精确软件复核；不冒充所有插件验收 |
| Erlang27.3.4.18 | 私有源码构建、crypto/SSL/public_key/asn1探测 | 所需OTP应用及OS库/许可对应；未选wx/ODBC等能力不能默认通过 |
| SeaweedFS4.48重建预选 | 精确Go构建输入/包图、候选摘要及有限扫描复核 | 按实际编入模块/内嵌材料复核义务和剩余风险，最终锁待准入；N03/N04存储恢复另验 |
| Keycloak26.8.1 | 生成物、字体/主题、40嵌套坐标及31特殊许可材料 | 对实际组合逐项作许可/安全准入决定；既有资料不是全阴影字节穷尽证明，N03/N05运行身份另验 |
| Java21.0.12.1+1 | 精确JDK、模块/TLS/headless及39份早期材料 | 按实际发行版核对GPL/Classpath例外、独立第三方部分及实际使用范围，不能由扫描零匹配直接签通过 |
| Nginx1.30.6 | 官方签名、源码构建/模块检查 | 实际链接TLS/其他库、编译模块及许可对应；N03代理/证书拒绝为后续功能验证 |
| age1.3.2重建预选 | 精确候选、Go输入及合成加密往返 | 编入模块/通知、实际准入及最终锁；正式公钥和恢复保管是后续N04，不在本轮提前生成 |

本表将N01制品准入与N02/N03/N04后续运行工作分开，后续步骤未执行不等于本轮应伪造其通过。原生包未安装不影响现有已验证研发继续开展满足依赖的任务。

## 当前答复与影响边界

2026-10-18用户希望继续使用Python3.10，并询问取消N01阻塞对项目影响是否很小；这是一项影响提问，未提供供应商延长维护证明，也不是明确的风险接受或整体准入决定。Python候选继续暂缓，现有解释器、原100包锁及共享服务不变。

当前已验证的Linux/py310/CPU内部研发可以继续开展满足依赖的工作；N01是全原生迁移的制品与软件准入步骤，其未通过不等于全部业务开发必须停下。现有功能通过测试只能证明已测功能在当前环境运行，不能证明未来维护、安全补丁、迁移恢复和正式交付风险很小。取消状态文字不会补齐技术证据，故保留N01的未通过状态；生产、离线及GPU仍另行验收。若未来提出有期限的研发例外，须单独明确用途、控制措施、责任、截止和退出条件，本次不代填或视为已批准。

| 编号 | 当前状态 | 后续动作 |
| --- | --- | --- |
| D01：Python3.10维护依据 | 已确认暂无维护或补丁支持证明；继续待处置，未接受风险 | 以后取得新材料时再核对发行者、精确版本与补丁范围；候选继续暂缓，本轮不重复询问。 |
| D02：下一批游标修复范围 | 用户明确答复“同意下一批按申请实施”；`IMPLEMENTED_VALIDATED_APPLICATION_SCOPE` | 本轮已按[批准申请](native-n01-cursor-hardening-change-request.md)完成代码、21项专项、隔离业务回归及检查，详见申请中的实际回执；无需重复确认同一范围。 |

D02授权不改变合法签发格式、密钥、端点或数据库结构，也不接受Python生命周期风险。授权、实现、测试通过和整体准入是不同状态；当前D02代码已实施并完成限定验证，运行服务未重启或切换。

## 以后才需要：当前不要一并批准

| 编号 | 时点与内容 |
| --- | --- |
| D03：整体软件准入 | Python维护/CVE和具体技术处置有证据后，再逐组件作实际决定。当前不要求“全部同意”，不能用审批掩盖技术缺口。 |
| D04：最终可安装锁 | 这是前置准入通过后由执行方完成的工作；三项预选已有确认，不需要重复选择。 |
| D05：N02管理员初始化 | N01通过、执行包就绪后再交徐昌胜操作；当前没有安装或sudo步骤。 |
| D06：N04备份公钥/保管 | 已明确徐昌胜保管且公钥尚未建立；到该步骤再按清单建立，不上传私钥。 |
| D07：停写、切换和实际运行发行 | 演练及接收范围明确后再决定窗口、保留与转交条件；当前不编造日期或对外运行发行许可。 |

已经确认的Python候选暂缓、三项原生制品预选、当前内部研发范围及此前有限材料复核均保留；不重复提问，也不扩大认可范围。生产、离线、Windows原生及GPU仍按原决定另行验收。

## 保留12条扫描记录：3条限定结论已认可，9条继续处置

下表沿用原逐项技术状态：3条限定不受影响技术历史记录、2条争议、7条行为或条件复核；其中3条当前目标限定不适用结论已获项目复核，原候选字段作为历史保留。原扫描与空缺的正式决定保留；“候选”“争议”都不自动变成安全通过。前轮31项特殊许可、40嵌套坐标及材料保留的[限定技术复核](native-n01-nested-license-use-review.md)仍有效，不重新写成尚未采集。

| CVE | 保留的技术状态 | 还需要的处置 |
| --- | --- | --- |
| CVE-2017-8806 | NOT_AFFECTED_CANDIDATE_PRODUCT_NOT_PRESENT | 当前目标限定不适用已获徐昌胜认可；保留原扫描，未来安装postgresql-common或改变产品集合须重新核验。 |
| CVE-2023-36632 | DISPUTED_REVIEW_REQUIRED | 确认实际邮件解析/输入限额与错误处理；争议不能直接当修复。 |
| CVE-2024-3220 | NOT_AFFECTED_CANDIDATE_PLATFORM | 当前Linux限定结论已获徐昌胜认可；Windows原生另审，原扫描保留。 |
| CVE-2025-12781 | OBSERVED_BEHAVIOR_APPLICATION_REVIEW_REQUIRED | D02已完成两处业务游标规范编码加固及验证；解释器未修补，其他调用和正式准入仍待复核 |
| CVE-2025-15366 | OBSERVED_COMMAND_BEHAVIOR_APPLICATION_REVIEW_REQUIRED | 不能声称当前模块已修补；核对正式用途和传递调用，采用受维护补丁或有时限的范围限制；启用邮件功能前必须处置。 |
| CVE-2025-15367 | OBSERVED_COMMAND_BEHAVIOR_APPLICATION_REVIEW_REQUIRED | 不能声称当前模块已修补；核对用途及传递调用，采用受维护补丁或范围限制；保留控制字符拒绝测试要求。 |
| CVE-2026-12003 | CONDITIONAL_SCOPE_REVIEW_REQUIRED | 还须核对父目录所有权/写权限、Conda补丁与启动策略；当前不存在不是长期不可利用证明。 |
| CVE-2026-12345 | CONDITIONAL_SCOPE_REVIEW_REQUIRED | 以非特权、私有0700目录和无不可信并发写入约束临时操作；核对源码修补、权限和使用者，不实施共享目录攻击。 |
| CVE-2026-3298 | NOT_AFFECTED_CANDIDATE_PLATFORM_AND_API | 当前Linux/py310及API范围限定结论已获徐昌胜认可；变更后重验，不扩大为整体安全准入。 |
| CVE-2026-3446 | OBSERVED_BEHAVIOR_APPLICATION_REVIEW_REQUIRED | D02已完成两处业务游标规范编码加固及验证；解释器未修补，其他调用和正式准入仍待复核 |
| CVE-2026-3479 | DISPUTED_REVIEW_REQUIRED | 不允许未授权路径作为resource；保留争议与软件准入决定。 |
| CVE-2026-6019 | OBSERVED_BEHAVIOR_APPLICATION_REVIEW_REQUIRED | 不将不可信cookie嵌入脚本；核对实际模板/传递调用，记录修补或有条件例外。 |

本页登记D02业务代码加固；解释器、依赖锁、服务、卷和数据库未修改；不增加170任务中的整任务验收数。后续依据D01实际证据及已批准D02范围推进相应工作，不自动实施后续业务任务或原生安装。
