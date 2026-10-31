export const styles = `
:host {
  all: initial;
  position: fixed;
  inset: 0;
  z-index: 2147483000;
  pointer-events: none;
  font-family: system-ui, sans-serif;
  color: #18181b;
}
* { box-sizing: border-box; }
button, textarea { font: inherit; color: inherit; }
.fab, .panel, .banner { pointer-events: auto; }
.fab {
  position: fixed;
  right: 20px;
  bottom: 20px;
  width: 56px;
  height: 56px;
  border: 0;
  border-radius: 999px;
  background: #c2410c;
  color: white;
  cursor: pointer;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18);
}
.panel {
  display: none;
  position: fixed;
  right: 20px;
  bottom: 20px;
  width: 380px;
  height: min(700px, calc(100vh - 40px));
  background: #fafafa;
  border: 1px solid #e4e4e7;
  border-radius: 16px;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.18);
  flex-direction: column;
  overflow: hidden;
  transform: translateY(20px);
  opacity: 0;
}
.panel.open, .panel.closing { display: flex; }
.panel.open { transform: none; opacity: 1; transition: transform 300ms ease, opacity 300ms ease; }
.panel.closing { transform: translateY(20px); opacity: 0; transition: transform 300ms ease, opacity 300ms ease; }
header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 12px 12px 16px;
  background: white;
  border-bottom: 1px solid #e4e4e7;
}
header strong { font-size: 15px; }
.close, .send, .choice {
  border: 0;
  background: transparent;
  cursor: pointer;
}
.close { width: 32px; height: 32px; border-radius: 8px; }
.close:hover { background: #f4f4f5; }
.banner {
  margin: 0;
  padding: 8px 16px;
  background: #fff7ed;
  color: #9a3412;
  font-size: 13px;
}
.log {
  flex: 1;
  overflow: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.bubble {
  max-width: 90%;
  padding: 10px 12px;
  border-radius: 14px;
  background: white;
  border: 1px solid #e4e4e7;
  line-height: 1.45;
  font-size: 14px;
}
.bubble.user { align-self: flex-end; background: #fff7ed; }
.bubble :first-child { margin-top: 0; }
.bubble :last-child { margin-bottom: 0; }
.hitl {
  align-self: stretch;
  background: white;
  border: 1px solid #e4e4e7;
  border-radius: 14px;
  padding: 12px;
}
.hitl h2 { margin: 0 0 6px; font-size: 15px; }
.hitl p { margin: 0; font-size: 14px; }
.actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 12px; }
.choice {
  border-radius: 999px;
  padding: 8px 12px;
  background: #f4f4f5;
}
.choice.primary { background: #c2410c; color: white; }
.choice:disabled { opacity: 0.5; cursor: default; }
.dots { display: flex; gap: 4px; padding: 4px 2px; }
.dots span {
  width: 6px;
  height: 6px;
  border-radius: 99px;
  background: #a1a1aa;
  animation: a2i-bounce 1s infinite;
}
.dots span:nth-child(2) { animation-delay: 0.15s; }
.dots span:nth-child(3) { animation-delay: 0.3s; }
@keyframes a2i-bounce {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
  40% { transform: translateY(-3px); opacity: 1; }
}
form {
  display: flex;
  gap: 8px;
  padding: 12px;
  background: white;
  border-top: 1px solid #e4e4e7;
}
textarea {
  flex: 1;
  resize: none;
  min-height: 44px;
  max-height: 96px;
  border: 1px solid #e4e4e7;
  border-radius: 12px;
  padding: 10px 12px;
}
.send {
  align-self: flex-end;
  height: 40px;
  padding: 0 14px;
  border-radius: 999px;
  background: #c2410c;
  color: white;
}
.send:disabled, textarea:disabled { opacity: 0.6; cursor: default; }
@media (max-width: 640px) {
  .panel.open, .panel.closing {
    width: 100vw;
    height: 100vh;
    right: 0;
    bottom: 0;
    border-radius: 0;
  }
  header { padding-top: max(12px, env(safe-area-inset-top)); }
}
`
