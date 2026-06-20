const { Stage, Sprite, useTime, Easing } = window;
const { VIDEO, ARTIFACTS, SKILL_FILES, SAFETY_BADGES, CLI_LINES } = window;

const palette = {
  bg: "#071117",
  bg2: "#0b1b24",
  panel: "rgba(12, 30, 39, 0.78)",
  panelStrong: "rgba(18, 42, 54, 0.92)",
  line: "rgba(117, 231, 255, 0.28)",
  cyan: "#6ee7ff",
  cyanSoft: "rgba(110, 231, 255, 0.18)",
  green: "#8df7b2",
  amber: "#ffd37a",
  text: "#f7fbff",
  muted: "#9db3bf",
  dim: "#59707d",
  red: "#ff7f8f",
};

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function smooth(start, end, time, ease) {
  if (time <= start) return 0;
  if (time >= end) return 1;
  const t = (time - start) / (end - start);
  return (ease || Easing.easeInOutCubic)(clamp(t, 0, 1));
}

function lerp(from, to, t) {
  return from + (to - from) * t;
}

function sectionProgress(time, start, end) {
  return clamp((time - start) / (end - start), 0, 1);
}

function titleStyle(size, extra) {
  return Object.assign({
    margin: 0,
    color: palette.text,
    fontFamily: "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
    fontWeight: 760,
    fontSize: size,
    letterSpacing: "-0.045em",
    lineHeight: 1.02,
  }, extra || {});
}

function copyStyle(size, extra) {
  return Object.assign({
    margin: 0,
    color: palette.muted,
    fontFamily: "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
    fontWeight: 500,
    fontSize: size,
    letterSpacing: "-0.01em",
    lineHeight: 1.35,
  }, extra || {});
}

function AmbientBackground() {
  const time = useTime();
  const drift = time * 0.035;
  const pulse = (Math.sin(time * 0.75) + 1) / 2;
  const glowX = 46 + Math.sin(time * 0.18) * 12;
  const glowY = 38 + Math.cos(time * 0.14) * 10;

  return (
    <div style={{ position: "absolute", inset: 0, overflow: "hidden", background: `radial-gradient(circle at ${glowX}% ${glowY}%, rgba(64, 209, 255, ${0.18 + pulse * 0.04}) 0, rgba(64, 209, 255, 0.06) 24%, rgba(7, 17, 23, 0) 48%), linear-gradient(145deg, ${palette.bg} 0%, ${palette.bg2} 58%, #09131b 100%)` }}>
      <div style={{
        position: "absolute",
        inset: -120,
        opacity: 0.42,
        backgroundImage: "linear-gradient(rgba(110,231,255,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(110,231,255,0.08) 1px, transparent 1px)",
        backgroundSize: "72px 72px",
        transform: `translate(${(drift * 72) % 72}px, ${(drift * 44) % 72}px)`,
      }} />
      <div style={{ position: "absolute", left: 128, top: 108, width: 420, height: 420, borderRadius: 999, background: "rgba(110,231,255,0.08)", filter: "blur(70px)", transform: `scale(${0.9 + pulse * 0.12})` }} />
      <div style={{ position: "absolute", right: 70, bottom: 80, width: 560, height: 560, borderRadius: 999, background: "rgba(141,247,178,0.07)", filter: "blur(86px)", transform: `translateY(${Math.sin(time * 0.22) * 24}px)` }} />
      <div style={{ position: "absolute", left: 92, right: 92, top: 72, bottom: 72, border: "1px solid rgba(110,231,255,0.10)", borderRadius: 36 }} />
    </div>
  );
}

function SceneLabel({ label, timecode }) {
  return (
    <div style={{ position: "absolute", left: 128, top: 96, display: "flex", gap: 14, alignItems: "center", color: palette.muted, fontFamily: "JetBrains Mono, ui-monospace, SFMono-Regular, Menlo, monospace", fontSize: 20, letterSpacing: "0.02em" }}>
      <span style={{ width: 10, height: 10, borderRadius: 99, background: palette.cyan, boxShadow: "0 0 24px rgba(110,231,255,0.9)" }} />
      <span>{label}</span>
      <span style={{ color: palette.dim }}>{timecode}</span>
    </div>
  );
}

function RepositoryIcon({ x, y, scale, active }) {
  const time = useTime();
  const pulse = active ? (Math.sin(time * 2.2) + 1) / 2 : 0.2;
  return (
    <div style={{ position: "absolute", left: x, top: y, width: 330 * scale, height: 250 * scale, transform: `translateY(${Math.sin(time * 0.8) * 6}px)`, filter: `drop-shadow(0 24px 60px rgba(0,0,0,0.35)) drop-shadow(0 0 ${18 + pulse * 20}px rgba(110,231,255,0.24))` }}>
      <div style={{ position: "absolute", left: 0, top: 38 * scale, width: 330 * scale, height: 212 * scale, borderRadius: 28 * scale, background: "linear-gradient(180deg, rgba(28,65,82,0.96), rgba(13,34,45,0.96))", border: `1px solid ${palette.line}` }} />
      <div style={{ position: "absolute", left: 22 * scale, top: 0, width: 142 * scale, height: 70 * scale, borderRadius: `${24 * scale}px ${24 * scale}px ${10 * scale}px ${10 * scale}px`, background: "linear-gradient(180deg, rgba(42,89,108,0.98), rgba(23,55,70,0.98))", border: `1px solid ${palette.line}` }} />
      {[0, 1, 2, 3].map((i) => (
        <div key={i} style={{ position: "absolute", left: 48 * scale, top: (92 + i * 34) * scale, width: (220 - i * 24) * scale, height: 9 * scale, borderRadius: 99, background: i === 0 ? palette.cyan : "rgba(247,251,255,0.20)" }} />
      ))}
    </div>
  );
}

function SkillCard({ x, y, width, height, title, subtitle, progress }) {
  const open = Easing.easeOutBack(clamp(progress, 0, 1));
  return (
    <div style={{ position: "absolute", left: x, top: y, width, height, borderRadius: 30, background: "linear-gradient(180deg, rgba(20,49,62,0.96), rgba(8,23,32,0.96))", border: `1px solid rgba(110,231,255,${0.18 + open * 0.42})`, boxShadow: `0 30px 80px rgba(0,0,0,0.35), 0 0 ${28 + open * 30}px rgba(110,231,255,0.15)`, opacity: open, transform: `translateY(${(1 - open) * 34}px) scale(${0.94 + open * 0.06})`, overflow: "hidden" }}>
      <div style={{ position: "absolute", inset: 0, background: "radial-gradient(circle at 85% 15%, rgba(110,231,255,0.20), transparent 36%)" }} />
      <div style={{ position: "relative", padding: 34 }}>
        <div style={{ color: palette.cyan, fontFamily: "JetBrains Mono, ui-monospace, monospace", fontSize: 22, marginBottom: 18 }}>AI AGENT SKILL PACK</div>
        <h3 style={titleStyle(48, { marginBottom: 12 })}>{title}</h3>
        <p style={copyStyle(24)}>{subtitle}</p>
        <div style={{ marginTop: 28, display: "grid", gap: 12 }}>
          {["Purpose", "Commands", "Workflows", "Validation", "Safety Notes"].map((name, i) => (
            <div key={name} style={{ display: "flex", alignItems: "center", gap: 12, opacity: smooth(i * 0.08, i * 0.08 + 0.22, open, Easing.easeOutCubic) }}>
              <span style={{ width: 9, height: 9, borderRadius: 99, background: i > 2 ? palette.green : palette.cyan }} />
              <span style={copyStyle(22, { color: palette.text })}>{name}</span>
              <span style={{ flex: 1, height: 1, background: "rgba(247,251,255,0.10)" }} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ArtifactCard({ name, index, reveal, x, y, variant }) {
  const t = smooth(index * 0.07, index * 0.07 + 0.35, reveal, Easing.easeOutBack);
  const color = variant === "skill" ? palette.green : variant === "warn" ? palette.amber : palette.cyan;
  return (
    <div style={{ position: "absolute", left: x, top: y, width: 310, height: 88, borderRadius: 18, background: palette.panel, border: `1px solid ${color === palette.cyan ? palette.line : "rgba(141,247,178,0.28)"}`, opacity: t, transform: `translateY(${(1 - t) * 28}px) rotate(${(1 - t) * -2}deg)`, boxShadow: "0 18px 42px rgba(0,0,0,0.22)", overflow: "hidden" }}>
      <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: 5, background: color }} />
      <div style={{ padding: "18px 22px 0 24px" }}>
        <div style={{ fontFamily: "JetBrains Mono, ui-monospace, monospace", color, fontSize: 15, marginBottom: 8 }}>{variant === "skill" ? "skill file" : "artifact"}</div>
        <div style={{ fontFamily: "JetBrains Mono, ui-monospace, monospace", color: palette.text, fontSize: 21, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{name}</div>
      </div>
    </div>
  );
}

function GraphNodes({ x, y, reveal }) {
  const nodes = [
    { id: "repo", label: "repo", px: 0, py: 80, r: 58, c: palette.cyan },
    { id: "docs", label: "docs", px: 230, py: 0, r: 44, c: palette.amber },
    { id: "scripts", label: "scripts", px: 392, py: 132, r: 48, c: palette.cyan },
    { id: "tests", label: "tests", px: 222, py: 260, r: 42, c: palette.green },
    { id: "rules", label: "safety", px: 510, py: 296, r: 50, c: palette.green },
  ];
  const links = [[0, 1], [0, 2], [0, 3], [2, 4], [3, 4]];
  return (
    <div style={{ position: "absolute", left: x, top: y, width: 620, height: 390 }}>
      <svg width="620" height="390" style={{ position: "absolute", inset: 0, overflow: "visible" }}>
        {links.map((link, i) => {
          const a = nodes[link[0]];
          const b = nodes[link[1]];
          const t = smooth(0.16 + i * 0.08, 0.38 + i * 0.08, reveal, Easing.easeOutCubic);
          return <line key={i} x1={a.px + 58} y1={a.py + 58} x2={lerp(a.px + 58, b.px + 50, t)} y2={lerp(a.py + 58, b.py + 50, t)} stroke="rgba(110,231,255,0.42)" strokeWidth="3" strokeLinecap="round" />;
        })}
      </svg>
      {nodes.map((node, i) => {
        const t = smooth(i * 0.09, i * 0.09 + 0.34, reveal, Easing.easeOutBack);
        return (
          <div key={node.id} style={{ position: "absolute", left: node.px, top: node.py, width: node.r * 2, height: node.r * 2, borderRadius: 999, display: "grid", placeItems: "center", color: palette.text, fontFamily: "JetBrains Mono, ui-monospace, monospace", fontSize: 18, background: "rgba(11,31,42,0.92)", border: `1px solid ${node.c}`, boxShadow: `0 0 ${24 + t * 22}px rgba(110,231,255,0.18)`, opacity: t, transform: `scale(${0.72 + t * 0.28})` }}>
            {node.label}
          </div>
        );
      })}
    </div>
  );
}

function SafetyBadge({ badge, index, reveal, compact }) {
  const t = smooth(index * 0.08, index * 0.08 + 0.28, reveal, Easing.easeOutBack);
  return (
    <div style={{ display: "flex", alignItems: "center", gap: compact ? 8 : 12, padding: compact ? "10px 14px" : "15px 20px", borderRadius: 999, background: "rgba(141,247,178,0.10)", border: "1px solid rgba(141,247,178,0.34)", color: palette.text, fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif", fontSize: compact ? 17 : 22, opacity: t, transform: `translateY(${(1 - t) * 12}px)` }}>
      <span style={{ width: compact ? 8 : 10, height: compact ? 8 : 10, borderRadius: 99, background: palette.green, boxShadow: "0 0 18px rgba(141,247,178,0.8)" }} />
      <span>{badge.label}</span>
      {!compact && <span style={{ color: palette.muted, fontSize: 18 }}>{badge.labelZh}</span>}
    </div>
  );
}

function PassStamp({ label, x, y, reveal, delay }) {
  const t = smooth(delay || 0, (delay || 0) + 0.28, reveal, Easing.easeOutBack);
  return (
    <div style={{ position: "absolute", left: x, top: y, width: 220, height: 92, display: "grid", placeItems: "center", color: palette.green, fontFamily: "JetBrains Mono, ui-monospace, monospace", fontSize: 34, fontWeight: 800, letterSpacing: "0.08em", border: "4px solid rgba(141,247,178,0.92)", borderRadius: 18, transform: `rotate(-7deg) scale(${0.55 + t * 0.45})`, opacity: t, boxShadow: "0 0 34px rgba(141,247,178,0.18)" }}>
      {label}
    </div>
  );
}

function Terminal({ x, y, width, height, reveal, lines }) {
  return (
    <div style={{ position: "absolute", left: x, top: y, width, height, borderRadius: 26, background: "rgba(4,12,18,0.92)", border: "1px solid rgba(110,231,255,0.26)", boxShadow: "0 34px 80px rgba(0,0,0,0.38)", overflow: "hidden" }}>
      <div style={{ height: 54, display: "flex", alignItems: "center", gap: 10, paddingLeft: 24, background: "rgba(255,255,255,0.04)", borderBottom: "1px solid rgba(255,255,255,0.07)" }}>
        {[palette.red, palette.amber, palette.green].map((c) => <span key={c} style={{ width: 14, height: 14, borderRadius: 99, background: c }} />)}
        <span style={{ marginLeft: 14, color: palette.dim, fontFamily: "JetBrains Mono, ui-monospace, monospace", fontSize: 16 }}>repo-to-skill demo</span>
      </div>
      <div style={{ padding: 30, fontFamily: "JetBrains Mono, ui-monospace, monospace", fontSize: 22, lineHeight: 1.6 }}>
        {lines.map((line, i) => {
          const t = smooth(i * 0.11, i * 0.11 + 0.2, reveal, Easing.easeOutCubic);
          const isResult = line.indexOf("PASS") >= 0 || line.indexOf("complete") >= 0 || line.indexOf("generated") >= 0;
          return (
            <div key={i} style={{ color: isResult ? palette.green : palette.text, opacity: t, transform: `translateX(${(1 - t) * -16}px)`, whiteSpace: "pre" }}>
              <span style={{ color: isResult ? palette.green : palette.cyan }}>{isResult ? "✓" : "$"}</span> {line}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function OpeningScene() {
  const time = useTime();
  const p = sectionProgress(time, 0, 9);
  const cards = ARTIFACTS.slice(0, 3);
  const flow = smooth(0.34, 0.72, p, Easing.easeInOutCubic);
  return (
    <Sprite start={0} end={9}>
      <SceneLabel label="Opening" timecode="00–09" />
      <div style={{ position: "absolute", left: 130, top: 190, width: 820 }}>
        <h1 style={titleStyle(70)}>Turn repository knowledge into an AI coding agent skill pack.</h1>
        <p style={copyStyle(30, { marginTop: 24, color: palette.text })}>把仓库知识转化为可复用的 AI 编程代理技能包。</p>
      </div>
      <RepositoryIcon x={205} y={590} scale={0.72} active />
      <div style={{ position: "absolute", left: 510, top: 710, width: 300, height: 3, background: "rgba(110,231,255,0.34)", transform: `scaleX(${flow})`, transformOrigin: "left" }} />
      {cards.map((name, i) => <ArtifactCard key={name} name={name} index={i} reveal={smooth(0.2, 0.68, p, Easing.easeOutCubic)} x={690 + i * 24} y={510 + i * 112} />)}
      <SkillCard x={1235} y={450} width={500} height={390} title="Repo to Skill" subtitle="A verified, reusable skill pack from local repository knowledge." progress={smooth(0.48, 0.9, p, Easing.easeOutCubic)} />
    </Sprite>
  );
}

function ProblemScene() {
  const time = useTime();
  const p = sectionProgress(time, 9, 20);
  const items = ["README", "scripts", "test commands", "release notes", "safety rules", "setup habits"];
  return (
    <Sprite start={9} end={20}>
      <SceneLabel label="Problem" timecode="09–20" />
      <div style={{ position: "absolute", left: 130, top: 190, width: 720 }}>
        <h2 style={titleStyle(66)}>Project knowledge is usually scattered.</h2>
        <p style={copyStyle(30, { marginTop: 24 })}>项目知识常常分散在文档、脚本、命令和约定里。</p>
      </div>
      {items.map((item, i) => {
        const t = smooth(0.08 + i * 0.05, 0.34 + i * 0.05, p, Easing.easeOutBack);
        const drift = Math.sin(time * 0.6 + i) * 10;
        return <ArtifactCard key={item} name={item} index={0} reveal={t} x={190 + (i % 2) * 360 + drift} y={485 + Math.floor(i / 2) * 116} variant={i > 3 ? "warn" : "artifact"} />;
      })}
      <div style={{ position: "absolute", right: 150, top: 250, width: 520, height: 540, borderRadius: 34, background: palette.panel, border: "1px solid rgba(247,251,255,0.12)", padding: 34 }}>
        <div style={{ color: palette.dim, fontFamily: "JetBrains Mono, ui-monospace, monospace", fontSize: 20, marginBottom: 28 }}>assistant context</div>
        {[0, 1, 2, 3, 4].map((i) => (
          <div key={i} style={{ height: 22, width: `${70 - i * 8}%`, borderRadius: 99, background: i === 1 ? "rgba(255,211,122,0.22)" : "rgba(247,251,255,0.10)", marginBottom: 24, opacity: 0.88 }} />
        ))}
        <div style={{ position: "absolute", left: 34, right: 34, bottom: 34, height: 104, borderRadius: 22, border: "1px dashed rgba(255,211,122,0.42)", color: palette.amber, display: "grid", placeItems: "center", fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif", fontSize: 26 }}>missing project behavior</div>
      </div>
    </Sprite>
  );
}

function LocalAnalysisScene() {
  const time = useTime();
  const p = sectionProgress(time, 20, 32);
  const loop = smooth(0.12, 0.5, p, Easing.easeOutCubic);
  return (
    <Sprite start={20} end={32}>
      <SceneLabel label="Local analysis" timecode="20–32" />
      <div style={{ position: "absolute", left: 130, top: 178, width: 720 }}>
        <h2 style={titleStyle(66)}>Local-first repository analysis.</h2>
        <p style={copyStyle(30, { marginTop: 24 })}>本地优先分析，不上传仓库。</p>
      </div>
      <RepositoryIcon x={210} y={510} scale={0.9} active />
      <div style={{ position: "absolute", left: 520, top: 620, width: 330, height: 3, borderRadius: 99, background: "rgba(110,231,255,0.38)", transform: `scaleX(${smooth(0.18, 0.52, p, Easing.easeOutCubic)})`, transformOrigin: "left" }} />
      <div style={{ position: "absolute", left: 565, top: 520, width: 270, height: 178, borderRadius: 28, background: "linear-gradient(180deg, rgba(20,49,62,0.94), rgba(8,23,32,0.94))", border: "1px solid rgba(110,231,255,0.36)", boxShadow: "0 28px 70px rgba(0,0,0,0.32), 0 0 30px rgba(110,231,255,0.12)", opacity: loop, transform: `translateY(${(1 - loop) * 18}px) scale(${0.94 + loop * 0.06})`, overflow: "hidden" }}>
        <div style={{ position: "absolute", inset: 0, background: "radial-gradient(circle at 85% 12%, rgba(110,231,255,0.18), transparent 44%)" }} />
        <div style={{ position: "relative", padding: "26px 28px" }}>
          <div style={{ color: palette.cyan, fontFamily: "JetBrains Mono, ui-monospace, monospace", fontSize: 17, letterSpacing: "0.08em", marginBottom: 18 }}>LOCAL ANALYSIS</div>
          <div style={{ color: palette.text, fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif", fontSize: 28, fontWeight: 720, lineHeight: 1.08 }}>Read-only scan</div>
          <div style={{ color: palette.muted, fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif", fontSize: 20, marginTop: 8 }}>本地只读扫描</div>
          <div style={{ marginTop: 22, display: "grid", gap: 9 }}>
            {["files", "commands", "rules"].map((label, i) => (
              <div key={label} style={{ display: "flex", alignItems: "center", gap: 10, opacity: smooth(0.28 + i * 0.08, 0.48 + i * 0.08, p, Easing.easeOutCubic) }}>
                <span style={{ width: 8, height: 8, borderRadius: 99, background: i === 2 ? palette.green : palette.cyan, boxShadow: "0 0 14px rgba(110,231,255,0.65)" }} />
                <span style={{ color: palette.text, fontFamily: "JetBrains Mono, ui-monospace, monospace", fontSize: 16 }}>{label}</span>
                <span style={{ flex: 1, height: 1, background: "rgba(247,251,255,0.13)" }} />
              </div>
            ))}
          </div>
        </div>
      </div>
      <GraphNodes x={870} y={350} reveal={smooth(0.18, 0.9, p, Easing.easeOutCubic)} />
      <div style={{ position: "absolute", left: 805, top: 770, display: "flex", gap: 14 }}>
        {SAFETY_BADGES.slice(0, 3).map((badge, i) => <SafetyBadge key={badge.label} badge={badge} index={i} reveal={smooth(0.42, 0.82, p, Easing.easeOutCubic)} compact />)}
      </div>
    </Sprite>
  );
}

function SkillGenerationScene() {
  const time = useTime();
  const p = sectionProgress(time, 32, 44);
  return (
    <Sprite start={32} end={44}>
      <SceneLabel label="Skill generation" timecode="32–44" />
      <div style={{ position: "absolute", left: 130, top: 170, width: 735 }}>
        <h2 style={titleStyle(64)}>Generate a reviewable AI agent skill pack.</h2>
        <p style={copyStyle(29, { marginTop: 24 })}>生成可审阅、可修改、可复用的 AI 代理技能包。</p>
      </div>
      <div style={{ position: "absolute", left: 155, top: 430 }}>
        {ARTIFACTS.slice(0, 3).map((name, i) => <ArtifactCard key={name} name={name} index={i} reveal={smooth(0.05, 0.46, p, Easing.easeOutCubic)} x={(i % 2) * 340} y={Math.floor(i / 2) * 108} />)}
      </div>
      <div style={{ position: "absolute", left: 830, top: 575, width: 160, height: 2, background: "rgba(110,231,255,0.40)", transform: `scaleX(${smooth(0.34, 0.62, p, Easing.easeOutCubic)})`, transformOrigin: "left" }} />
      <SkillCard x={1035} y={310} width={620} height={500} title="launch-skill" subtitle="Plain files, readable workflows, validation hints, and safety notes." progress={smooth(0.48, 0.86, p, Easing.easeOutBack)} />
    </Sprite>
  );
}

function ValidationScene() {
  const time = useTime();
  const p = sectionProgress(time, 44, 55);
  const badges = SAFETY_BADGES.slice(0, 3);
  return (
    <Sprite start={44} end={55}>
      <SceneLabel label="Validation and safety" timecode="44–55" />
      <div style={{ position: "absolute", left: 130, top: 168, width: 780 }}>
        <h2 style={titleStyle(68)}>Validate before you trust it.</h2>
        <p style={copyStyle(31, { marginTop: 24 })}>先验证，再信任。</p>
      </div>
      <div style={{ position: "absolute", left: 146, top: 425, display: "grid", gap: 18 }}>
        {badges.map((badge, i) => <SafetyBadge key={badge.label} badge={badge} index={i} reveal={smooth(0.05, 0.46, p, Easing.easeOutCubic)} />)}
      </div>
      <div style={{ position: "absolute", right: 150, top: 260, width: 640, height: 520, borderRadius: 34, background: palette.panelStrong, border: "1px solid rgba(110,231,255,0.28)", boxShadow: "0 32px 86px rgba(0,0,0,0.34)", padding: 38 }}>
        <div style={{ color: palette.cyan, fontFamily: "JetBrains Mono, ui-monospace, monospace", fontSize: 22, marginBottom: 28 }}>verification_report.json</div>
        {["schema check", "artifact coverage", "eval case"].map((row, i) => {
          const t = smooth(0.18 + i * 0.07, 0.34 + i * 0.07, p, Easing.easeOutCubic);
          return (
            <div key={row} style={{ display: "flex", alignItems: "center", gap: 18, height: 58, opacity: t, transform: `translateX(${(1 - t) * -18}px)`, color: palette.text, fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif", fontSize: 25 }}>
              <span style={{ width: 22, height: 22, borderRadius: 99, background: palette.green, boxShadow: "0 0 18px rgba(141,247,178,0.58)" }} />
              <span>{row}</span>
              <span style={{ marginLeft: "auto", color: palette.green, fontFamily: "JetBrains Mono, ui-monospace, monospace" }}>PASS</span>
            </div>
          );
        })}
      </div>
      <PassStamp label="PASS" x={1290} y={695} reveal={smooth(0.58, 0.92, p, Easing.easeOutCubic)} />
      <PassStamp label="EVAL PASS" x={1458} y={610} reveal={smooth(0.68, 0.98, p, Easing.easeOutCubic)} delay={0.12} />
    </Sprite>
  );
}

function RealCliScene() {
  const time = useTime();
  const p = sectionProgress(time, 55, 66);
  const cliLines = CLI_LINES.map((line) => line.command).concat(["analysis complete", "generated reviewable skill", "validate PASS", "eval PASS"]);
  return (
    <Sprite start={55} end={66}>
      <SceneLabel label="Real CLI" timecode="55–66" />
      <div style={{ position: "absolute", left: 130, top: 166, width: 640 }}>
        <h2 style={titleStyle(70)}>Real CLI. Real workflow.</h2>
        <p style={copyStyle(31, { marginTop: 24 })}>真实 CLI，真实工作流。</p>
      </div>
      <Terminal x={125} y={380} width={1040} height={520} reveal={smooth(0.08, 0.9, p, Easing.easeOutCubic)} lines={cliLines} />
      <SkillCard x={1235} y={390} width={520} height={430} title="validated skill" subtitle="Review what it creates, then bring project knowledge into your coding agent." progress={smooth(0.48, 0.88, p, Easing.easeOutBack)} />
    </Sprite>
  );
}

function ClosingScene() {
  const time = useTime();
  const p = sectionProgress(time, 66, 75);
  const flow = smooth(0.18, 0.74, p, Easing.easeInOutCubic);
  return (
    <Sprite start={66} end={75}>
      <SceneLabel label="Closing" timecode="66–75" />
      <div style={{ position: "absolute", left: 130, top: 168, width: 920 }}>
        <h2 style={titleStyle(72)}>Build project knowledge into your assistant.</h2>
        <p style={copyStyle(32, { marginTop: 24, color: palette.text })}>把项目知识沉淀进你的开发助手。</p>
      </div>
      <RepositoryIcon x={230} y={515} scale={0.78} active />
      <div style={{ position: "absolute", left: 575, top: 640, width: 330, height: 3, background: "rgba(110,231,255,0.34)", transform: `scaleX(${flow})`, transformOrigin: "left" }} />
      <SkillCard x={860} y={470} width={420} height={330} title="Skill" subtitle="Local-first. Reviewable. Validated." progress={smooth(0.28, 0.62, p, Easing.easeOutBack)} />
      <div style={{ position: "absolute", left: 1310, top: 585, width: 220, height: 220, borderRadius: 46, background: "rgba(110,231,255,0.12)", border: "1px solid rgba(110,231,255,0.40)", display: "grid", placeItems: "center", opacity: smooth(0.48, 0.82, p, Easing.easeOutBack), transform: `scale(${0.86 + smooth(0.48, 0.82, p, Easing.easeOutBack) * 0.14})` }}>
        <div style={{ color: palette.text, fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif", fontSize: 32, fontWeight: 740, textAlign: "center", lineHeight: 1.1 }}>AI<br />Agent</div>
      </div>
      <div style={{ position: "absolute", left: 130, right: 130, bottom: 112, display: "flex", justifyContent: "center", gap: 14 }}>
        {SAFETY_BADGES.slice(0, 2).map((badge, i) => <SafetyBadge key={badge.label} badge={badge} index={i} reveal={smooth(0.42, 0.9, p, Easing.easeOutCubic)} compact />)}
      </div>
      <div style={{ position: "absolute", right: 132, top: 170, color: palette.cyan, fontFamily: "JetBrains Mono, ui-monospace, monospace", fontSize: 30, opacity: smooth(0.6, 0.95, p, Easing.easeOutCubic) }}>repo-to-skill</div>
    </Sprite>
  );
}

function LaunchVideo() {
  return (
    <Stage width={VIDEO.width} height={VIDEO.height} duration={VIDEO.duration} background={palette.bg}>
      <AmbientBackground />
      <OpeningScene />
      <ProblemScene />
      <LocalAnalysisScene />
      <SkillGenerationScene />
      <ValidationScene />
      <RealCliScene />
      <ClosingScene />
    </Stage>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<LaunchVideo />);
