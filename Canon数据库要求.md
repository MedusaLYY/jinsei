# 第 VXXX 卷 Canon Enrichment 深度构建要求

## 一、目标

当前处理：

data/canon_enriched/VXXX.json


目标：

不是人物百科。

而是服务于：
- AI GM
- 世界模拟器
- 原著角色反事实推演


数据库必须回答：

这个角色是谁？
这个阶段知道什么？
不知道什么？
相信什么？
为什么这么行动？
面对玩家不同选择会如何反应？


---

## 二、数据来源原则

所有数据必须来自：

原著文本

流程：

原文
↓
Evidence
↓
Canon判断
↓
结构化数据


禁止：

- 凭模型印象补充
- 为填字段编造
- 用泛化标签替代细节
- 固定数量生成


原则：

正确性 > 可追溯性 > 完整性 > 数量


---

## 三、需要构建的数据


### 1. CharacterProfile

记录：

- 身份
- 年龄阶段
- 性格
- 价值观
- 目标
- 恐惧
- 动机
- 风险倾向
- 决策倾向
- 社交方式
- 公开人格
- 私人人格


每个字段必须：

- evidence_refs
- confidence


---

### 2. CharacterQuirk / PrivateBehavior


记录：

- 怪癖
- 小习惯
- 私人兴趣
- 收藏
- 特殊反应
- 羞耻点
- 愤怒表现
- 紧张动作
- 喜欢/讨厌


必须区分：

public_expression

private_expression


---

### 3. BehaviorCase


每个重要角色需要记录：

- 事件背景
- 触发因素
- 当时知道的信息
- 当时不知道的信息
- 目标
- 行动
- 语言
- 情绪
- 结果
- 后续影响


覆盖：

- 战斗
- 冲突
- 愤怒
- 恐惧
- 羞耻
- 信任
- 背叛
- 家庭
- 爱情
- 权威
- 谈判
- 失败
- 成功


---

### 4. Knowledge系统


必须区分：

world_truth

character_knowledge

character_belief

rumor

false_belief

unknown


角色不能知道数据库里的所有信息。


---

### 5. Relationship


不能只有：

朋友
敌人
师徒


需要：

- trust
- respect
- fear
- loyalty
- dependency
- attraction
- resentment
- gratitude
- obligation


并且：

A→B

和：

B→A

可以不同。


---

### 6. SpeechProfile


记录：

- 说话习惯
- 称呼方式
- 语气
- 玩笑方式
- 生气方式
- 害羞方式
- 拒绝方式
- 对不同对象的区别


---

## 四、Evidence要求


重大结论必须有 Evidence。


Evidence类型：

CANON_EXPLICIT

STRONG_INFERENCE

INFERENCE

UNKNOWN


禁止：

没有文本依据的人格判断。


---

## 五、禁止出现的问题


禁止：

- “第X卷新增见闻”
- “第X卷习得技能”
- “经历使人物成长”
- “关系加深”
- “性格成熟”

这种空泛描述。


禁止：

为了数量：

- 每卷固定生成多少条
- 每章固定生成多少条


不同卷数量自然变化。


---

## 六、游戏化数据边界


Canon不要写：

HP
MP
攻击力
魅力数值


Canon负责：

原著事实和人格。


Engine负责：

游戏数值。


---

## 七、本卷完成验收


完成 VXXX 后：

随机选择主要角色。

测试：

如果玩家做出原著没有发生的新行为：

AI是否可以根据：

- CharacterProfile
- BehaviorCase
- Relationship
- Knowledge
- Quirk
- SpeechProfile
- Evidence

推演合理反应。


如果只能依靠模型记忆：

说明 Canon 不合格。


---

## 八、最终目标


让 AI 不是“知道这个角色”。

而是：

在改变原著剧情后，

仍然能够像这个角色本人一样：

思考、
说话、
行动。