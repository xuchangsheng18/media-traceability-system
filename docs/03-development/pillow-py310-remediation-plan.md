# Pillow／py310兼容修复方案与隔离验证计划

> 2026-10-21执行更新：D05-E隔离范围已获确认。PL01已完成源码层回移/静态核验；PL02因构建闭包和namespace探针未通过，PL03—PL05尚未执行。当前事实见[隔离实施回执](pillow-py310-isolated-execution.md)，下文保留形成方案时的依据与批准计划。

> 后续执行工具：仅在本方案的隔离执行范围获确认后，使用 executing-plans 或 subagent-driven-development 逐项实施。下列PL编号不是170项源任务编号。

**方案形成日期：2026-10-21；当时状态：未执行回补、构建或漏洞回归，未批准采用。后续执行见页首回执。** 本方案归入T016环境依赖收口；任务责任沿用已登记的徐昌胜，不自动授予软件准入批准权限。T016仍为4项已验证子步骤、4组剩余，整卡未关闭。

**Goal：**逐项确定8条Pillow漏洞的py310处理路径、回归和准入条件，防止把私有回补或扫描跳过误记为可采用修复。

**Architecture：**以Pillow 12.3.0为回移基线，只移植可追溯的局部修复及必要前置；保留原解释器、ABI、业务接口和功能范围。技术候选验证、漏洞数据库识别、正式采用三者分别决策。

**Tech Stack：**当前Linux x86_64／Miniforge Python 3.10.22／CPU；原锁Pillow 12.3.0；Pillow原生C扩展、libtiff等实际编解码依赖。Windows继续作为远程开发入口，本方案不做Windows原生包或GPU验收。

**Spec：**本文件第1—6节；实际来源和逐项机器记录见[只读研究记录](../00-project/validation/t016-pillow-py310-plan-review.json)。

## 1. 结论及执行边界

八条的上游修复版本均指向13.0.0；[官方Python支持表](https://pillow.readthedocs.io/en/stable/installation/python-support.html)和[13.0.0元数据](https://pypi.org/pypi/pillow/13.0.0/json)要求Python≥3.11。不能强制忽略Requires-Python，也不能把cp311包改标签当cp310包。

静态源码比较支持“局部回移值得验证”的判断，**不证明11项必要提交已经适用、能编译、修复有效或可通过现有准入门禁**。当前没有已核实的、可同时满足py310和现有默认扫描的正式修复发行。

方案形成批仅完成：原8条识别、官方公告／修复代码／测试的只读核对、当前Linux安装元数据采样、路线与回归编制、文档导航检查。未执行：源码打补丁、编译、安装、漏洞样本、漏洞回归、候选联调、原锁修改、共享迁移或服务重启。

全局约束：

- 原`config/locks/requirements-py310.lock`、`config/versions.yaml`和现有CI工作流／门禁保持字节不变；Python 3.13／3.12候选继续暂缓。
- 只允许后续获确认的独立源码和包目录；同一个既有py310解释器不等于可以向其site-packages写入候选。
- 不删除Pillow、编解码器或安全测试以规避匹配；不加ignore-vuln、假版本号、宽松断言或未知版本skip来获取通过。
- 当前certifi 2026.10.19只经隔离验证，未采用；原100包锁仍保留certifi 1条＋Pillow 8条的实际扫描记录。Torch原skip及N01原CPython 9条是另外两类未决项。
- 本方案及其只读核验不计为8条漏洞已修复，不增加170任务完成数量，不构成T013接管、N01整体准入、生产或外发批准。

## 2. 当前基线、项目入口与处理路线

### 2.1 已核对的输入

| 输入 | 精确基线／含义 |
| --- | --- |
| 规划前源码 | `e77b24f23e9253991b74884e51575952c617ad1a`；本文件并不证明其未来提交的CI。 |
| Python／Pillow | 当前Linux只读采样为3.10.22／12.3.0；安装元数据Requires-Python≥3.10。 |
| 原100包锁 | SHA-256 `dbbb604b912342e4fec69ca27db6f99047737947386dd7ce2bb460a82cdbdcf8`。 |
| 原versions.yaml | SHA-256 `5d80c8c002584c9ba91e7fadbcc5f63c8b4dc5004082d188acc874d16afa8b8a`。 |
| 后续源码制品来源 | [官方12.3.0元数据](https://pypi.org/pypi/pillow/12.3.0/json)中的sdist `pillow-12.3.0.tar.gz`，47,025,035字节，SHA-256 `3b8182a766685eaa002637e28b4ec8d6b18819a0c71f579bf0dbaa5830297cce`；本轮只核元数据，未下载或执行该归档。 |
| 当前C库线索 | features读取到libtiff 4.7.1、OpenJPEG 2.5.4、WebP 1.6.0、FreeType 2.14.3等；`jpg=6.2`是接口报告，不能当libjpeg-turbo精确补丁版本。实际wheel有两份SBOM，完整编译／链接来源仍需PL02核对。 |
| Ghostscript | 当前宿主机PATH中未发现`gs`，不覆盖容器或后续安装，也不能据此关闭EPS库漏洞。 |

### 2.2 项目入口的实际边界

[业务上传校验](../../backend/business_app/uploads/validator.py)先调用`Image.open`，随后检查PNG／JPEG、声明MIME和4,000,000像素，再verify并重新load；[PoC入口](../../backend/app/common.py)也在open后检查。格式过滤不等于解析器选择前的隔离，更不能据此关闭库级漏洞。

[PoC分析副本](../../backend/app/main.py)会convert／thumbnail／保存PNG；[推理入口](../../ai-services/inference/service.py)会open／convert／resize。未找到项目对PdfParser、ImageMorph或EPS scale的直接调用，只能说明本次静态检索未见该入口，不代表动态插件、依赖调用或后续功能绝对不可达。

### 2.3 路线比较

| 路线 | 当前判定与采用条件 |
| --- | --- |
| 维护方发布真实py310补丁发行，漏洞数据同步识别 | **正式准入主路线。** 必须有可核验源码／制品、维护责任和8条修复范围；PyPI及现有查询链识别后，按原门禁扫描、另审采用。本轮未取得此发行或维护承诺。 |
| 内部12.3.0局部回移 | **可选技术验证路线。** 先静态移植11项必要变更，再在受限私有构建与回归中验证；必须诚实标识私有派生来源。即使技术通过，当前默认门禁仍不能自动认可它。 |
| 直接采用13.0.0／更换Python | 与当前py310及Python候选暂缓决定冲突，本轮不执行；不得修改元数据／wheel标签伪装兼容。 |

不把“供应商维护”当作已有事实。若后续选择向维护方询问，需单独授权实际联系；本轮未发送邮件、issue或评论。

## 3. 八条漏洞逐项处理与回归

以下记录形成方案时的**PLANNED_NOT_FIXED**状态。现已授权的源码层回移见页首回执，仍未编译或验证运行时修复，8条均未关闭。上游测试名用于追溯；未来必须在实际cp310候选上执行并保留nodeid、源摘要、退出码、失败／跳过及资源证据。

### 3.1 CVE-2026-112895：PDF页树与trailer递归

依据：[官方公告](https://github.com/python-pillow/Pillow/security/advisories/GHSA-p4wg-p73j-c528)、[CNA记录](https://github.com/CVEProject/cvelistV5/blob/main/cves/2026/112xxx/CVE-2026-112895.json)。受影响≥5.1.0、<13.0.0。既有PDF以`append=True`进入解析器时，循环／重复页引用与长Prev链可消耗栈和资源；不是只保存新PDF就已证明触发。

处理组合：trailer迭代[852d834491c7ecd252b5072f5d8d18d3bba3f72b](https://github.com/python-pillow/Pillow/commit/852d834491c7ecd252b5072f5d8d18d3bba3f72b)、页树去重[6f0e7ee1f9c2fe227906f8a4b926e6622b702bc7](https://github.com/python-pillow/Pillow/commit/6f0e7ee1f9c2fe227906f8a4b926e6622b702bc7)、依赖该去重的迭代遍历[e2ae7eacad6de68c37eb28b633a97bebacf2c5bf](https://github.com/python-pillow/Pillow/commit/e2ae7eacad6de68c37eb28b633a97bebacf2c5bf)。修改范围`src/PIL/PdfParser.py`及`Tests/test_pdfparser.py`；不能只移植最后一项。

回归：保留`test_long_trailer_chain`、`test_trailer_loop`、`test_linearize_page_tree_duplicate_reference`、`test_linearize_page_tree_deep`。正常增量PDF页序／已有内容保持；循环和重复引用按PdfFormatError拒绝；1001条trailer、2000层合法页树在受限进程完成且无RecursionError；分别统计耗时、句柄和资源增长。独立解析器不能共享visited状态，同文件并发append仍需应用文件锁。不得把迭代改写描述为统一深度上限，也不宣称Prev列表查找已变成严格线性复杂度。

### 3.2 CVE-2026-112400：GIF拒绝尺寸被提前提交

依据：[官方公告](https://github.com/python-pillow/Pillow/security/advisories/GHSA-65qm-jvmh-6pqg)、[CNA记录](https://github.com/CVEProject/cvelistV5/blob/main/cves/2026/112xxx/CVE-2026-112400.json)。CNA范围≥9.2.0、<13.0.0，比公告页的宽泛上界更具体。捕获后续帧DecompressionBombError后复用对象，可能保留被拒绝尺寸；不能扩称所有普通open/load都已复现。

处理：[6faed707cfb760a4cbd726ddc8406f576cf35bf7](https://github.com/python-pillow/Pillow/commit/6faed707cfb760a4cbd726ddc8406f576cf35bf7)，在`GifImagePlugin.py`先检查局部候选尺寸、后赋`_size`。上游`TestDecompressionBomb.test_exception_gif_extents`位于`Tests/test_decompression_bomb.py`。

回归：降低仅本进程测试阈值，确认失败seek不提交新尺寸、不按拒绝尺寸分配；检查size、底层缓冲、tell、重试／reseek／load各自实际行为，不能把size断言当完整状态回滚。合法帧扩大、调色板和disposal输出保持；重复拒绝后句柄／内存稳定。并发只处理独立对象，修改全局MAX_IMAGE_PIXELS的测试必须进程隔离，禁止线程间改阈值。

### 3.3 CVE-2026-112397：ImageMorph空尺寸C写越界

依据：[官方公告](https://github.com/python-pillow/Pillow/security/advisories/GHSA-58r4-6rv3-gfh8)、[CNA记录](https://github.com/CVEProject/cvelistV5/blob/main/cves/2026/112xxx/CVE-2026-112397.json)。范围<13.0.0；空宽图进入MorphOp.apply可在行边界写越界并崩溃。

处理：[18f7c0dfee93063c51db6ed0ca8c4da2999dcb64](https://github.com/python-pillow/Pillow/commit/18f7c0dfee93063c51db6ed0ca8c4da2999dcb64)，`src/_imagingmorph.c`在宽／高为零时提前返回。对应`Tests/test_imagemorph.py::test_zero_width`。需要重编C扩展，不能只替换Python文件。

回归：覆盖(0,N)、(N,0)、(0,0)，输出模式／尺寸／像素保持且changed count为0；1、2像素边界与普通形态结果／边界值保持。非法mode、LUT和capsule维持既有拒绝；ASan或等效原生内存检查无越界，重复和独立对象并发无污染／泄漏。match/get_on_pixels补空尺寸回归，但只读源码未证实公告所述“同样边界写”，不得冒充另一已复现漏洞。

### 3.4 CVE-2026-112896：TIFF ColorMap保存越界读

依据：[官方公告](https://github.com/python-pillow/Pillow/security/advisories/GHSA-pchr-8j38-3x4p)、[CNA记录](https://github.com/CVEProject/cvelistV5/blob/main/cves/2026/112xxx/CVE-2026-112896.json)。范围<13.0.0；保留ColorMap的TIFF经libtiff保存时，固定256项平面步长与实际BitsPerSample不符，可能读出堆内容。单纯打开图片不是该保存路径的完整复现。

处理：[d03dc3c587a9b0bdc9e4304d70d59a635a87b742](https://github.com/python-pillow/Pillow/commit/d03dc3c587a9b0bdc9e4304d70d59a635a87b742)及颜色保真后续[0e546950c3d00cb7bcb033e18d49c6ee48c08988](https://github.com/python-pillow/Pillow/commit/0e546950c3d00cb7bcb033e18d49c6ee48c08988)，共同覆盖`TiffImagePlugin.py`两条编码路径、`src/encode.c`和`Tests/test_file_libtiff.py`。

回归：`test_colormap_size_mismatch`与`test_palette_save`必须保留**非零RGB平面逐值／像素比较**，不能只比长度或全零图。覆盖P／PA、I;16、8位768项和16位196608项、libtiff开关两路径；错误长度、缺失／异常BitsPerSample应在native复制前确定拒绝。ASan／内存检查无越界读，失败不泄漏；不同位深独立编码器并发无步长串用。全局WRITE_LIBTIFF开关按进程隔离，不并发切换。

### 3.5 CVE-2026-112897：TIFF短JPEG块泄漏未初始化像素

依据：[官方公告](https://github.com/python-pillow/Pillow/security/advisories/GHSA-q45j-58j2-45rg)、[CNA记录](https://github.com/CVEProject/cvelistV5/blob/main/cves/2026/112xxx/CVE-2026-112897.json)。范围≥5.3.0、<13.0.0；JPEG strip／tile实际行数短于目录声明而libtiff仍报告成功时，返回像素可能含未写入堆内容。

处理：[1d4773e6cea0c4a2814e6d4cdc099bbcf56da6ce](https://github.com/python-pillow/Pillow/commit/1d4773e6cea0c4a2814e6d4cdc099bbcf56da6ce)，修改`src/libImaging/TiffDecode.c`。实际提交只清零realloc新增长区域，并非每次读取前清空全部buffer；保留赋值次序及这一边界。

回归：`TestFileLibTiff.test_jpeg_short_strip[tiled=False/True]`应验证前8行像素200、后248行0；同时覆盖完整块、块复用、灰度／RGB、planar和适用Group4。失败读取必须抛OSError并释放资源。ASan不能证明没有未初始化读取，需MSan或Valgrind等覆盖该类问题；不支持相应诊断时该项保持未验证。独立图片并发、失败后再解码不能串入其他请求像素；不能宣称同一Image对象并发load安全。

### 3.6 CVE-2026-112395：TIFF tile存储量不匹配越界读

依据：[官方公告](https://github.com/python-pillow/Pillow/security/advisories/GHSA-462x-pgg6-55fp)、[CNA记录](https://github.com/CVEProject/cvelistV5/blob/main/cves/2026/112xxx/CVE-2026-112395.json)。范围≥8.2.0、<13.0.0；tile存储量小于解包需求时，旧检查可能让行解包越过分配尾部。

处理：[d01e2fe0f02a0293018c27eb3288b3511675bd89](https://github.com/python-pillow/Pillow/commit/d01e2fe0f02a0293018c27eb3288b3511675bd89)将单向大小检查改为不等即拒绝，并与下一条行宽修复组合审查；不能只改一个比较符就宣称覆盖全部TIFF布局问题。

回归：保留`TestFileLibTiff.test_tiled_jpeg_oob_read`的load抛OSError断言，补确定解码错误及无堆像素输出；过小／过大tile、零行宽、行宽大于块、极端乘法均受限拒绝。有效JPEG／YCbCr subsampling、边缘tile和分平面像素保持。监测分配前拒绝、原生越界和资源释放；独立合法／异常对象混合并发不互相污染。上游图片仅作为待核验夹具引用，本轮未下载或运行。

### 3.7 CVE-2026-112404：TIFF行解包宽度超过libtiff行宽

依据：[官方公告](https://github.com/python-pillow/Pillow/security/advisories/GHSA-c6hw-5grf-ff96)、[CNA记录](https://github.com/CVEProject/cvelistV5/blob/main/cves/2026/112xxx/CVE-2026-112404.json)。范围≥8.1.0、<13.0.0；解析出的模式与libtiff布局不一致，tile或RGBA路径可越界读取源行。

处理：[76869efdbbf2ad7dccd7536520fb61b7a00ab61e](https://github.com/python-pillow/Pillow/commit/76869efdbbf2ad7dccd7536520fb61b7a00ab61e)，接在d01e2fe上下文后审查`TiffDecode.c`。tile按tsize_t计算并检查行宽；实际RGBA条件是`state->bits != 32`，不能误写成仅大于32。

回归：采用修复提交中的`test_unpacker_row_wider_than_libtiff_row`并补12.3可达的布局/C边界用例；行需求等于实际行允许，大于实际行拒绝；RGBA位数小于／大于32均拒绝。有效tile／strip／16位图保持；极端算术、失败释放和并发独立对象均检查。后续[重复标签解析变更](https://github.com/python-pillow/Pillow/commit/27af434ef326fd5f71e600ba39c86c5706526fc3)改变最终13.0.0同名测试的触发层；不能只移植最终测试的早期解析拒绝，就声称C守卫已覆盖。

### 3.8 CVE-2026-112899：EPS scale绕过渲染前像素预算

依据：[官方公告](https://github.com/python-pillow/Pillow/security/advisories/GHSA-vx6w-vv9f-6gvg)。其affected字段为2.3.0—12.3.0，正文追溯2.5.0，保留此来源差异；两者均包含当前12.3.0。本轮CVEProject原始镜像返回404，未伪造CNA记录，改用已核对官方公告及修复提交。

处理：[3e8cc105588d1dfe062fcada0b6058c1b5f14b65](https://github.com/python-pillow/Pillow/commit/3e8cc105588d1dfe062fcada0b6058c1b5f14b65)，在`EpsImagePlugin.Ghostscript`计算缩放尺寸后检查像素预算，先于渲染和输出临时文件创建。

回归：`test_load_scale_decompression_bomb`通过受控spy保证越限时不调用渲染check_call、不创建渲染输出；明确这不是实际Ghostscript成功渲染测试。分别检查恰好MAX不告警、MAX＜像素数≤2MAX的warning（含恰好2MAX）、超过2MAX的error，以及warning转error策略；scale=1、正常scale、直接函数调用及既有无gs错误语义保持。可能先发生gs版本探测，不能笼统写“绝无子进程”。若未来环境实际支持EPS，还须隔离验证真实gs正常渲染／超时／清理；当前宿主机未发现gs不等于漏洞已关闭。

## 4. 补丁组合、构建来源和许可

### 4.1 最小必要集合与邻接项

8条共对应**11项必要修复／前置／纠偏提交**：PDF三项、GIF一项、ImageMorph一项、ColorMap两项、TIFF短块／tile／行宽各一项、EPS一项。保留各自上游提交、前后源码和patch摘要，按上游父图及上述依赖移植；遇到上下文冲突先解释，不使用整份13.0.0模块覆盖12.3.0。

TIFF三条应组合审查，不能把CNA的references字段当一对一补丁证明：本轮112395 CNA引用`76869ef`，112404 CNA引用`1d4773`；本方案依据CNA正文、真实代码行为及上游测试，将tile存储量、行宽、未初始化像素分别对应`d01e2fe`、`76869ef`、`1d4773`。保留这项引用差异及各自完整来源，不擅自更改原记录，也不据单个引用省略另两项修复。

PDF对象嵌套上限／rewrite_pages循环、TIFF重复标签解析等邻接修复应单独列来源及所属公告。它们不自动并入最小集合，也不算本批8条的替代证据。执行前重新读取维护方当前公告全集；发现新增适用问题另列，不能把此次扫描8条当作全部原生库漏洞总数。

### 4.2 构建清单的硬条件

- 源码锁记录sdist／不可变tag commit、11项patch及前置、test-images和pillow-depends的不可变提交／归档hash；不使用官方脚本中的可变`main.zip`作为复现输入。
- [12.3.0 pyproject](https://github.com/python-pillow/Pillow/blob/12.3.0/pyproject.toml)实际为`build-backend="backend"`、`backend-path=["_custom_build"]`，要求pybind11及setuptools≥77。原锁已有build 1.6.1、setuptools 84.0.0、wheel 0.48.0、packaging 26.3、pytest 9.1.1、NumPy 2.2.6；不是新建包工具锁的自动批准。缺少的pybind11、原生工具及诊断器必须在PL02形成独立精确版本／制品hash清单，缺项则PL03禁止开始。
- 编译／链接器、CPython头文件／ABI、glibc、编译flags、RPATH、libtiff及其补丁、JPEG／zlib／OpenJPEG／WebP／FreeType／lcms／AVIF传递库全部进入清单。不能只锁Pillow版本，也不能把libtiff裸4.7.1或JPEG ABI字符串当完整补丁状态。
- 保留现有必要功能，实际记录构建特性与wheel SBOM；官方libtiff补丁等pedigree要逐项核验。libimagequant原官方轮设置为disable，不得意外引入GPLv3组件；FriBiDi shim等LGPL材料、Pillow MIT-CMU和其他捆绑许可逐项保留，项目Apache-2.0不覆盖它们。
- 输出必须真实cp310-cp310／目标Linux x86_64可导入；不重贴cp311标签、不修改Requires-Python规避限制。至少两次清洁构建比较产物及差异，不在仅成功编译一次后宣称可复现。
- 候选目录须在仓库和共享解释器之外，测试使用同一既有解释器及显式候选路径，并检查`PIL.__file__`、C扩展路径和实际链接库。退出候选进程后重新核对原Pillow文件、原锁和共享Git状态。

### 4.3 回滚与停止条件

当前没有部署，隔离回退是停止候选进程并撤销仅该进程的候选搜索路径，验证原字节／导入路径仍相同；不得覆盖原包后再把重装当“无变更”。后续任何真实采用需另立环境备份、准确旧制品、切换窗口与恢复回执，本方案未批准该步骤。

若缺补丁前置、构建／许可输入、可验证的进程隔离／CPU／内存／临时盘限额、诊断器或必要codec，停止受影响步骤，不把skip或模拟结果记为该漏洞通过。ASan/MSan等虚拟地址要求须与隔离预算相容，不能用阻止诊断器启动的地址空间限制制造假阴性。

## 5. 保留门禁时的准入判定

现行[scripts/stage_three_quality.py](../../scripts/stage_three_quality.py)对**原requirements锁**运行pip-audit，Python findings>0即阻断；未知包skip只记录。当前原锁扫描仍是certifi 1＋Pillow 8，不能用已验证但未采用的certifi候选结果覆盖它。

[pip-audit 2.10.1的PyPI查询](https://github.com/pypa/pip-audit/blob/v2.10.1/pip_audit/_service/pypi.py)按名字和精确版本访问PyPI；本轮查询私有local版本及未发布12.3.1为404，URL依赖也可变为skip。因此：

| 输入或动作 | 必须给出的严格结论 |
| --- | --- |
| 原锁12.3.0不变，仅私下修库文件 | 扫描依然匹配；还破坏制品一致性，不可作为采用路线。 |
| 诚实标注私有local版本的回补轮 | 可供隔离技术验证；PyPI未知／新增skip不得算零匹配准入。候选新增Pillow skip必须在独立评审中阻断，不能利用原门禁的覆盖限制。 |
| 改名、假报13.0.0、去掉依赖或忽略CVE | 不接受；版本／SBOM／消费者依赖与事实不符。 |
| 真实受维护py310修复发行＋8条范围被数据维护者识别 | 再核实时扫描和skip，逐项回归、许可／来源，另行批准准确锁与环境采用；不得预填目前尚不存在的发行。 |

每个CVE分别保存：源码回补状态、实际回归状态、工具与数据库时间、版本匹配／skip、采用状态。VEX或供应商证明可作为技术评审附件，**不把它自动接进当前门禁的豁免规则**。当前8条记录均不关闭。

原工作流、required engineering、90分钟时限、所有正常／拒绝／故障探针及第三阶段13项运行验证均保持。文档检查通过不等于整体CI通过；方案提交若触发新CI，以实际SHA和run记录，不把上一条失败隐藏或预填未来结果。

## 6. 最低回归与审查关注点

1. 八个必需测试族任何一个缺失、零收集或skip都不能通过候选技术评审；上游其他可选特性skip须单列依据，不能补作这八族证据。
2. C越界使用ASan/UBSan等，未初始化读另用MSan或Valgrind等；解释器/C依赖未被有效诊断时明确标未验证。
3. 有效PNG／JPEG及现有4,000,000像素边界、截断JPEG、声明MIME/摘要拒绝、verify后重开load、对象/数据库/队列失败及幂等回滚保留原断言。
4. 原始文件保持、独立分析副本、PNG/RGB/L变换、thumbnail／resize、NumPy输入和既有合成CPU推理结果按原用例核对，不把合成模型当真实业务准确率。
5. 全局阈值／WRITE_LIBTIFF等测试进程隔离；独立对象并行与失败清理不等于同对象线程安全。原生缺陷样例仅在另批受限隔离环境，以自建无敏感或经hash核验的公开夹具执行。

应用层可另行考虑在插件选择前显式限制获准格式、统一像素／资源和异常处理；当前`Image.open`前的防护并未实现。本方案不暗中改动API行为、阈值或业务模块，也不把此类减缓等同库修复。

## 7. 原批准隔离实施分步（当前实际状态见页首回执）

运行根`ROOT`由后续runner在项目私有runtime中创建唯一目录并写入manifest，禁止位于原源码／共享env内。下列qa文件均为**计划创建位置**，当前不存在，命令是未来验证要求。

### PL01：固定源码和11项补丁的真实派生关系

Files：`ROOT/manifest/source.json`、`ROOT/src/`、`ROOT/patches/`、`ROOT/qa/check_source.py`。

- [ ] 获取并核验第2节源码hash、上游commit与夹具来源；清点11项patch文件及每条CVE对应关系。
- [ ] 先保留原12.3.0静态断言RED，再做patch dry-run和逐hunk移植；缺PDF去重、ColorMap颜色纠偏或TIFF行宽前置必须拒绝，不能模糊匹配强套。
- [ ] `python -B qa/check_source.py --manifest manifest/source.json`验证全部SHA／前置／源码差异，缺一项应明确失败；产出只标静态结果，不标漏洞修复通过。

### PL02：闭合工具、C库、许可证及可验证隔离预算

Files：`ROOT/manifest/build-tools.json`、`ROOT/manifest/native-libraries.json`、`ROOT/licenses/`、`ROOT/qa/check_build_inputs.py`。

- [ ] 固定实际py310 ABI、原生工具／build工具及全部C库的精确版本、来源、hash、补丁、flags／功能矩阵及许可证；不依赖latest或隐式联网构建。
- [ ] 演示缺制品hash、缺native许可、可变分支或缺codec会失败；`python -B qa/check_build_inputs.py --offline`通过后才允许PL03。
- [ ] 候选安全样例的CPU／内存／临时盘／超时在manifest中给出可执行硬上限及实际隔离探针；当前未设置任何共享配额。隔离不可验证时停止样例运行，不能在共享进程试探漏洞。

### PL03：私有cp310构建及清洁重建

Files：`ROOT/build-tools/`、`ROOT/deps/`、`ROOT/dist/`、`ROOT/site/`、`ROOT/manifest/build-output.json`、`ROOT/qa/build_candidate.py`、`ROOT/qa/check_wheel.py`。

- [ ] 批准后只在上述独立目录准备依赖；同一原解释器不写共享site-packages，不新建3.13／3.12解释器环境。
- [ ] `python -B qa/build_candidate.py --manifest manifest/source.json --offline`按PL02准确工具清单调用原PEP517 backend，无隐式build isolation联网拉latest。
- [ ] `python -B qa/check_wheel.py --manifest manifest/build-output.json --python /opt/conda/glwy/envs/py310/bin/python`从构建manifest读取唯一实际wheel及hash，检查真实ABI、RECORD、来源／许可证／SBOM、动态链接和候选导入路径，不猜文件名。
- [ ] 两次清洁构建核对差异；私有派生版本不得伪装官方发行。缺C依赖修补／许可证／可复现证据时停止，不发布候选。

### PL04：八族修复回归、正常行为及原生诊断

Files：`ROOT/qa/test_eight_cve_backports.py`、`ROOT/qa/run_security_regressions.py`、`ROOT/qa/fixtures-manifest.json`、`ROOT/reports/`。

- [ ] 计划必需函数：`test_pdf_append_graph_guards`、`test_gif_rejected_extent_no_size_commit`、`test_morph_empty_no_native_oob`、`test_tiff_colormap_nonzero_roundtrip`、`test_tiff_short_jpeg_defined_pixels`、`test_tiff_tile_storage_matches`、`test_tiff_unpacker_rows_match`、`test_eps_scaled_budget_before_render`；分别落实第3节的参数化断言和原上游测试。
- [ ] 在获确认且硬隔离有效的独立进程，先验证RED能捕获目标缺陷，再验证候选GREEN；C缺陷不得在当前共享解释器环境的正常业务进程中复现。
- [ ] `python -B qa/run_security_regressions.py --mandatory-cve-manifest manifest/source.json`须检查完整收集、无必需skip、实际候选路径、独立诊断器结果及内存／时间／句柄证据；脚本未创建前不得声称此命令已执行。
- [ ] 对EPS分别记录无需实际渲染的前置拒绝断言与实际gs联调范围；无gs或spy通过不当成gs正常渲染通过。

### PL05：项目私有联调与准确的扫描解释

Files：`ROOT/project-snapshot/`、`ROOT/qa/check_project_binding.py`、`ROOT/reports/project/`。

- [ ] 在私有项目快照绑定候选；确认测试进程、API、worker、推理及任何镜像各自真实加载的Pillow／C扩展／库，避免只替测试进程换包却声称全栈采用。
- [ ] 保留现有业务／权限／范围／令牌、上传与推理回归；按适用私有服务执行原验证命令并分别记录，不向共享库初始化或升级。
- [ ] 重读当前8条及新增适用公告、扫描完整依赖和native SBOM；记录Pillow新skip即不准入。Torch旧skip单列，不能掩盖新增Pillow skip。
- [ ] 原source lock未采用时，正常GitHub CI仍查询原版本。私有镜像或本地harness结果只能证明候选子范围，不能替代原CI完整成功。

### PL06：技术结论、维护责任与采用评审

Files：`ROOT/reports/technical-review.json`、`ROOT/reports/adoption-request.json`及本仓库后续实际回执。

- [ ] 分别列出8条代码／回归／scanner／维护／许可状态；仅技术通过时登记`TECHNICAL_CANDIDATE_ONLY`，不关闭漏洞或源任务。
- [ ] 取得真实可识别修复发行、数据范围和维护责任后，再提交准确环境／原锁／镜像变更、备份回退和窗口供单独批准。
- [ ] 采用获批准后才改实际版本锁并执行完整工程CI及13项runtime，核验确切SHA、实际制品和所有故障探针。当前未授权这一步。

## 8. 需要用户确认及外部条件

**本轮方案和导航同步无需补充账号、密码或密钥。** 后续若继续执行，需确认：

- D05-E：用户已确认按PL01—PL05在独立目录开展技术回移／构建／回归；遇到PL02输入或隔离能力不足就停止对应步骤，不安装共享依赖、不改原锁、不创建Python候选。无需重复确认同一隔离范围；确认不等于预计8条能在原门禁内关闭。
- D05-M：维护方／正式识别修复发行目前未取得；若要联系上游或供应商，需另行明确授权实际发送，或提供已有正式补丁来源。缺少该条件时，允许只做技术候选并保留CI阻塞，不伪造维护承诺。
- D05-A：任何共享采用、准确锁替换、镜像及切换窗口属于未来独立批准；当前不要求提前批准未知制品。

以上是原规划状态；授权后的源码回移、静态检查及未执行项以页首回执为准。8条逐项状态、来源快照与当前CI实际观察通过[本批进度](../00-project/validation/t016-development-progress.json)、[机器核对记录](../00-project/validation/t016-pillow-py310-plan-review.json)以及[T016任务卡](../../tasks/platform/T016.md)同步；正式判断仍以实际证据及该卡关闭条件为准。
