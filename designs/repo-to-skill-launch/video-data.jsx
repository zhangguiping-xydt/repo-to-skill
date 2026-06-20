const VIDEO = {
  width: 1920,
  height: 1080,
  duration: 75,
  title: "Repo to Skill Launch",
  subtitle: "Turn a repository into a verified, reusable AI coding agent skill pack",
  subtitleZh: "将仓库转化为可验证、可复用的 AI 编程代理技能包",
};

const ARTIFACTS = [
  "scan.json",
  "profile.json",
  "capability_evidence.json",
  "capability_graph.json",
  "skill_spec.yaml",
  "verification_report.json",
  "confidence-report.md",
];

const SKILL_FILES = [
  "SKILL.md",
  "manifest.yaml",
  "scripts/inspect_repo.py",
  "references/project-map.md",
  "references/capability-graph.md",
  "references/skill-spec.md",
  "references/confidence-report.md",
];

const SAFETY_BADGES = [
  { label: "Read-only helpers", labelZh: "只读辅助脚本" },
  { label: "No source upload", labelZh: "不上传源码" },
  { label: "No remote DB", labelZh: "不需要远程数据库" },
  { label: "No default vector DB", labelZh: "默认不使用向量数据库" },
];

const CLI_LINES = [
  {
    key: "compose",
    label: "Compose",
    command: "repo-to-skill compose ./demo-repo",
  },
  {
    key: "analyze",
    label: "Analyze",
    command: "repo-to-skill analyze ./demo-repo",
  },
  {
    key: "generate",
    label: "Generate",
    command: "repo-to-skill generate ./artifacts",
  },
  {
    key: "validation",
    label: "Validate",
    command: "repo-to-skill validate ./launch-skill",
  },
  {
    key: "eval",
    label: "Evaluate",
    command: "repo-to-skill eval --case tiny-python",
  },
];

Object.assign(window, {
  VIDEO,
  ARTIFACTS,
  SKILL_FILES,
  SAFETY_BADGES,
  CLI_LINES,
});
