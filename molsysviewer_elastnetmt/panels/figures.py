from __future__ import annotations

from typing import Any

from molsysviewer import AddonPanelWidget

from ..runtime import ensure_runtime, record_event

_PRESETS = [
    {"id": "structure_network", "label": "Structure + Network"},
    {"id": "structure_mode", "label": "Structure + Mode Vectors"},
    {"id": "structure_anisotropy", "label": "Structure + Anisotropy"},
    {"id": "full", "label": "All Active Overlays"},
]

_ESM = """
const PRESETS = [
  { id: "structure_network",    label: "Structure + Network" },
  { id: "structure_mode",       label: "Structure + Mode Vectors" },
  { id: "structure_anisotropy", label: "Structure + Anisotropy" },
  { id: "full",                 label: "All Active Overlays" },
];

export function render({ model, el }) {
  let state = {
    active_preset: "structure_network",
    format: "png",
    overlays: [],
    status: "idle",
    error: null,
  };

  el.innerHTML = `
    <div class="enm-fig-panel">
      <div class="enm-field">
        <label class="enm-label">Preset</label>
        <select class="enm-select" id="enm-preset"></select>
      </div>
      <div class="enm-field">
        <label class="enm-label">Format</label>
        <div class="enm-tabs" id="enm-fmt-tabs" role="tablist">
          <button class="enm-tab enm-tab--active" data-fmt="png" role="tab">PNG</button>
          <button class="enm-tab" data-fmt="html" role="tab">HTML</button>
        </div>
      </div>
      <div class="enm-overlays" id="enm-overlays"></div>
      <button class="enm-btn enm-btn--primary" id="enm-export">Export Figure</button>
      <div class="enm-status" id="enm-status"></div>
    </div>
  `;

  const presetSel = el.querySelector("#enm-preset");
  const fmtTabs = el.querySelectorAll(".enm-tab[data-fmt]");
  const overlaysEl = el.querySelector("#enm-overlays");
  const exportBtn = el.querySelector("#enm-export");
  const statusEl = el.querySelector("#enm-status");

  PRESETS.forEach(({ id, label }) => {
    const opt = document.createElement("option");
    opt.value = id;
    opt.textContent = label;
    presetSel.appendChild(opt);
  });

  function applyState(s) {
    state = { ...state, ...s };

    presetSel.value = state.active_preset;
    fmtTabs.forEach((btn) => {
      btn.classList.toggle("enm-tab--active", btn.dataset.fmt === state.format);
    });

    if (state.overlays.length > 0) {
      overlaysEl.innerHTML =
        `<div class="enm-label">Active overlays</div>` +
        state.overlays.map((o) => `<div class="enm-overlay-tag">${o}</div>`).join("");
    } else {
      overlaysEl.innerHTML = "";
    }

    exportBtn.disabled = state.status === "exporting";
    exportBtn.textContent = state.status === "exporting" ? "Exporting…" : "Export Figure";

    if (state.status === "done") {
      statusEl.textContent = "Figure exported";
      statusEl.className = "enm-status enm-status--ok";
    } else if (state.status === "error" && state.error) {
      statusEl.textContent = `Error: ${state.error}`;
      statusEl.className = "enm-status enm-status--error";
    } else if (state.status === "exporting") {
      statusEl.textContent = "Exporting…";
      statusEl.className = "enm-status enm-status--busy";
    } else {
      statusEl.textContent = "";
      statusEl.className = "enm-status";
    }
  }

  presetSel.addEventListener("change", () => {
    model.send({ type: "action", id: "set_preset", payload: { preset: presetSel.value } });
  });

  fmtTabs.forEach((btn) => {
    btn.addEventListener("click", () => {
      model.send({ type: "action", id: "set_format", payload: { format: btn.dataset.fmt } });
    });
  });

  exportBtn.addEventListener("click", () => {
    model.send({
      type: "action",
      id: "export",
      payload: { preset: state.active_preset, format: state.format },
    });
  });

  model.on("msg:custom", (msg) => {
    if (msg?.type === "state") applyState(msg.state);
  });

  model.send({ type: "query", id: "viewer.context" });

  applyState(state);
}
"""

_CSS = """
.enm-fig-panel {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px;
  font-size: 13px;
  font-family: sans-serif;
}
.enm-field {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.enm-label {
  font-size: 11px;
  opacity: 0.7;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.enm-select {
  padding: 4px 6px;
  border: 1px solid #555;
  background: transparent;
  color: inherit;
  border-radius: 4px;
  font-size: 13px;
}
.enm-tabs {
  display: flex;
  gap: 4px;
}
.enm-tab {
  flex: 1;
  padding: 4px 8px;
  border: 1px solid #555;
  background: transparent;
  color: inherit;
  cursor: pointer;
  border-radius: 4px;
}
.enm-tab--active {
  background: #3a7bd5;
  border-color: #3a7bd5;
  color: #fff;
}
.enm-overlays {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.enm-overlay-tag {
  font-size: 11px;
  opacity: 0.8;
  padding: 2px 4px;
  border-left: 2px solid #3a7bd5;
}
.enm-btn--primary {
  padding: 5px 10px;
  background: #3a7bd5;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}
.enm-btn--primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.enm-status {
  font-size: 11px;
  min-height: 16px;
}
.enm-status--ok { color: #4caf50; }
.enm-status--error { color: #f44336; }
.enm-status--busy { opacity: 0.7; }
"""


class ElastNetMTFiguresPanel(AddonPanelWidget):
    _esm: str = _ESM
    _css: str = _CSS

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._active_preset: str = "structure_network"
        self._active_format: str = "png"

    def on_mount(self, view: Any) -> None:
        runtime = ensure_runtime(view)
        self.push_state(self._build_state(runtime))

    def handle_action(self, view: Any, action_id: str, payload: dict) -> None:
        runtime = ensure_runtime(view)

        if action_id == "set_preset":
            preset = payload.get("preset", self._active_preset)
            if isinstance(preset, str):
                self._active_preset = preset
                self.push_state(self._build_state(runtime))

        elif action_id == "set_format":
            fmt = payload.get("format", self._active_format)
            if fmt in ("png", "html"):
                self._active_format = fmt
                self.push_state(self._build_state(runtime))

        elif action_id == "export":
            preset = payload.get("preset", self._active_preset)
            fmt = payload.get("format", self._active_format)
            self.push_state({**self._build_state(runtime), "status": "exporting"})
            try:
                result = self._run_export(view, runtime, preset, fmt)
                record_event(
                    view, "panel_export_figure", preset=preset, format=fmt, **result
                )
                self.push_state({**self._build_state(runtime), "status": "done"})
            except Exception as exc:
                self.push_state(
                    {**self._build_state(runtime), "status": "error", "error": str(exc)}
                )

    def _run_export(self, view: Any, runtime: Any, preset: str, fmt: str) -> dict:
        from ..export import build_figure_export_payload

        payload = build_figure_export_payload(view)
        payload["selected_preset"] = preset
        payload["selected_format"] = fmt

        overlays = list(runtime.visible_overlays)
        if preset == "structure_network":
            overlays = [o for o in overlays if "contacts" in o]
        elif preset == "structure_mode":
            overlays = [o for o in overlays if "mode" in o]
        elif preset == "structure_anisotropy":
            overlays = [o for o in overlays if "anisotropy" in o]

        payload["figure_recipe"]["visible_overlays"] = overlays
        return {"n_overlays": len(overlays)}

    def _build_state(self, runtime: Any) -> dict:
        return {
            "active_preset": self._active_preset,
            "format": self._active_format,
            "overlays": list(runtime.visible_overlays),
            "status": "idle",
            "error": None,
        }
