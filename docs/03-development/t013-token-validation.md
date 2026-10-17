# T013 第一批：访问令牌核验与身份映射

日期：2026-10-17。任务为“实现认证与令牌校验”，责任角色为后端/安全；实际负责人未登记。本批实现可选的远端令牌核验适配器和现有数据库身份映射，正式身份协议尚未选定，整任务保持未关闭。

[任务卡](../../tasks/platform/T013.md) · [实际验证报告](../00-project/validation/t013-token-validation-report.json) · [身份关系](../04-database/identity-relations.md)

## 依据、依赖和实施范围

读取本卡、AGENTS、ER-T013、TV-T013-N/E、业务OpenAPI中devLogin/getCurrentUser及现有认证端口；复用T012的0004身份映射、0005角色目录、IdentityDirectory和Database。原始任务要求见任务卡引用；本批没有重新逐页审核Word原件，不宣称完成新的源件审查。

本批读取T012已归档实施/测试证据，并在本批完整回归中重新执行其身份、角色目录和迁移测试。T012正式规则及整任务验收仍待落实；本批仅使用其已实现并验证的数据库技术范围。

可选适配依据[RFC 7662](https://www.rfc-editor.org/rfc/rfc7662.html)，不代表项目正式决定使用OAuth或某一身份产品。该规范允许资源服务向认证服务查询令牌当前状态。实现使用现有锁中的httpx 0.28.1，不新增运行依赖，不改变原100包锁、数据库结构及外部接口。

## 当前行为

1. 调用方显式构造IntrospectionSettings和IntrospectionVerifier，提供固定HTTPS核验地址、预期issuer/audience、客户端凭据、超时及报文/令牌大小限制。未知业务参数不填默认正式值；凭据从Git外注入。
2. 仅向配置地址POST表单令牌及access_token提示；使用客户端Basic认证，凭据先按OAuth客户端认证要求编码。禁止地址含userinfo、查询参数或片段，禁止跟随重定向和环境代理，保留证书校验。
3. 有效身份必须满足active严格为true、精确issuer、匹配audience、有效sub、Bearer类型、整数exp尚未到期，以及适用nbf/iat检查。这里要求的issuer/audience/exp/token_type是本可选适配器的严格集成配置要求，不宣称都是RFC必选响应字段。
4. 核验响应大小受限，重复JSON键、错误类型、非JSON、上游错误及超时均拒绝；不回显上游正文、令牌或客户端秘密。不在日志或证据中保存真实令牌。
5. 每次认证重新核验远端状态，再通过独立mt_identity_lookup连接调用既有mt.resolve_identity；只接受已启用、未撤销、未到期的精确issuer/subject映射及有效用户/单位。连接不得为超级用户、BYPASSRLS或目录管理角色；查询失败返回受控503。
6. 数据库查询后再次检查令牌有效期；不缓存令牌或映射成功。下次认证可以观察到上游失效及数据库禁用/撤销，但不承诺未确认的远端撤销SLA，也不追溯中止已经开始的业务操作。
7. 只构造内部Actor。令牌内roles/scope不会直接授予案件或来源访问；相关判断继续委托独立AuthorityProvider。未提供该策略时返回FORMAL_POLICY_UNCONFIGURED，不返回业务允许。

## 接入及修改边界

新增实现为backend/business_app/identity/tokens.py。由可信启动代码创建只具身份查询权限的Database与核验器，构造MappedTokenAuthority后，显式传给既有create_app的authority参数；生命周期由调用方管理，退出时关闭核验器和查询连接池。create_app默认不安装该适配器，现有部署继续拒绝缺失身份的动作。

本批没有登录签发、密码存储、刷新令牌、退出/撤销HTTP接口、正式授权种子或人员管理审计。现有/auth/me仍需独立目录适配器，不能把获得Actor当作已交付完整用户权限系统。远端撤销API和密钥轮换协议需随实际身份方接入另行定义；未知接口不自行新增到业务OpenAPI。

## 验证与验收口径

- tests/platform/test_t013_tokens.py：合成HTTP传输核验请求方法/凭据编码、有效与无效声明、过期、未生效、重复字段、响应大小、重定向、超时、报文及配置拒绝、每次重新核验。
- tests/business/test_token_identity.py：真实隔离PostgreSQL和仅查询角色，核验有效映射、禁用用户/单位、映射撤销/禁用/到期、错误issuer/未映射身份、上游inactive、缺权限、管理连接拒绝、查询期间过期。
- 这些测试使用合成身份与HTTP MockTransport，数据库是真实实例；没有连接正式IdP、没有验证其TLS部署、真实签名或私钥、登录和撤销接口。伪造令牌由权威服务判定inactive的集成语义已覆盖，不能据此声称完成正式签名防伪测试。
- 实际命令、版本、数量、源码摘要和失败修复记录以报告为准；新实现不得借用旧CI数量宣称已通过新验证。

## 剩余条件与恢复

仍需确定正式认证协议、issuer、audience、可信核验端点与凭据管理、撤销SLA，完成登录/签发或统一身份重定向方案、真实生命周期联调、安全与权限回归、负责人/工时及有效验收。默认拒绝和合成适配测试不等于整项T013完成。本批不执行T014。

本批无数据库迁移和共享服务重启，源码同步不等于运行部署。回退可撤销本批代码提交；若后续显式安装适配器，先撤销安装配置并重新验证默认拒绝，再关闭其HTTP与数据库连接。生产profile仍按既有配置拒绝启动。
## 后续设计关联（2026-10-17）

[自建Keycloak身份系统完整设计](t013-keycloak-identity-design.md)已形成，方向获认可、书面设计待审阅。本页首批适配器及其历史验证范围保持不变；私有CA信任装配、真实Keycloak接入和部署均尚未完成。
