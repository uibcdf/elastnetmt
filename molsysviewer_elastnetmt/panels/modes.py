from __future__ import annotations

from typing import Any

from molsysviewer import AddonPanelWidget

from ..runtime import ensure_runtime, record_event

_ESM = """
export function render({ model, el }) {
  let state = {
    mode_index: 0,
    n_modes: null,
    model_kind: "gnm",
    status: "idle",
    error: null,
  };

  el.innerHTML = `
    <div class="enm-modes-panel">
      <div class="enm-field">
        <label class="enm-label">Mode index</label>
        <div class="enm-mode-row">
          <button class="enm-icon-btn" id="enm-prev" title="Previous mode">&#8592;</button>
          <input class="enm-input enm-input--num" type="number" id="enm-mode-idx" min="0" step="1" />
          <button class="enm-icon-btn" id="enm-next" title="Next mode">&#8594;</button>
        </div>
        <div class="enm-mode-count" id="enm-mode-count"></div>
      </div>
      <button class="enm-btn enm-btn--primary" id="enm-show">Show Vectors</button>
      <div class="enm-status" id="enm-status"></div>
    </div>
  `;

  const idxInput = el.querySelector("#enm-mode-idx");
  const prevBtn = el.querySelector("#enm-prev");
  const nextBtn = el.querySelector("#enm-next");
  const showBtn = el.querySelector("#enm-show");
  const countEl = el.querySelector("#enm-mode-count");
  const statusEl = el.querySelector("#enm-status");

  function applyState(s) {
    state = { ...state, ...s };

    if (document.activeElement !== idxInput) {
      idxInput.value = state.mode_index;
    }
    idxInput.max = state.n_modes !== null ? state.n_modes - 1 : "";

    countEl.textContent =
      state.n_modes !== null ? `of ${state.n_modes} modes (${state.model_kind.toUpperCase()})` : "";

    showBtn.disabled = state.status === "rendering";
    showBtn.textContent = state.status === "rendering" ? "Rendering…" : "Show Vectors";

    if (state.status === "done") {
      statusEl.textContent = `Mode ${state.mode_index} rendered`;
      statusEl.className = "enm-status enm-status--ok";
    } else if (state.status === "error" && state.error) {
      statusEl.textContent = `Error: ${state.error}`;
      statusEl.className = "enm-status enm-status--error";
    } else if (state.status === "rendering") {
      statusEl.textContent = "Rendering…";
      statusEl.className = "enm-status enm-status--busy";
    } else {
      statusEl.textContent = "";
      statusEl.className = "enm-status";
    }
  }

  idxInput.addEventListener("change", () => {
    const idx = parseInt(idxInput.value, 10);
    if (!isNaN(idx) && idx >= 0) {
      model.send({ type: "action", id: "set_mode_index", payload: { mode_index: idx } });
    }
  });

  prevBtn.addEventListener("click", () => {
    const idx = Math.max(0, state.mode_index - 1);
    model.send({ type: "action", id: "set_mode_index", payload: { mode_index: idx } });
  });

  nextBtn.addEventListener("click", () => {
    const max = state.n_modes !== null ? state.n_modes - 1 : Infinity;
    const idx = Math.min(max, state.mode_index + 1);
    model.send({ type: "action", id: "set_mode_index", payload: { mode_index: idx } });
  });

  showBtn.addEventListener("click", () => {
    model.send({ type: "action", id: "show_mode_vectors", payload: { mode_index: state.mode_index } });
  });

  model.on("msg:custom", (msg) => {
    if (msg?.type === "state") applyState(msg.state);
  });

  model.send({ type: "query", id: "viewer.context" });

  applyState(state);
}
"""

_CSS = """
.enm-modes-panel {
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
.enm-mode-row {
  display: flex;
  align-items: center;
  gap: 4px;
}
.enm-icon-btn {
  width: 28px;
  height: 28px;
  border: 1px solid #555;
  background: transparent;
  color: inherit;
  cursor: pointer;
  border-radius: 4px;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.enm-input {
  padding: 4px 6px;
  border: 1px solid #555;
  background: transparent;
  color: inherit;
  border-radius: 4px;
  font-size: 13px;
}
.enm-input--num {
  width: 64px;
}
.enm-mode-count {
  font-size: 11px;
  opacity: 0.6;
  min-height: 14px;
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


class ElastNetMTModesPanel(AddonPanelWidget):
    _esm: str = _ESM
    _css: str = _CSS

    def on_mount(self, view: Any) -> None:
        runtime = ensure_runtime(view)
        self.push_state(self._build_state(runtime, view))

    def handle_action(self, view: Any, action_id: str, payload: dict) -> None:
        runtime = ensure_runtime(view)

        if action_id == "set_mode_index":
            idx = payload.get("mode_index")
            if isinstance(idx, int) and idx >= 0:
                runtime.active_mode_index = idx
                record_event(view, "panel_set_mode_index", mode_index=idx)
                self.push_state(self._build_state(runtime, view))

        elif action_id == "show_mode_vectors":
            idx = payload.get("mode_index", runtime.active_mode_index)
            self.push_state({**self._build_state(runtime, view), "status": "rendering"})
            try:
                n_vectors = self._run_show_vectors(view, runtime, idx)
                record_event(
                    view, "panel_show_mode_vectors", mode_index=idx, n_vectors=n_vectors
                )
                self.push_state({**self._build_state(runtime, view), "status": "done"})
            except Exception as exc:
                self.push_state(
                    {
                        **self._build_state(runtime, view),
                        "status": "error",
                        "error": str(exc),
                    }
                )

    def _run_show_vectors(self, view: Any, runtime: Any, mode_index: int) -> int:
        from ..adapters.modes import render_mode_vectors

        molsys = getattr(view, "_molsys", None) or getattr(
            view, "molecular_system", None
        )
        if molsys is None:
            raise RuntimeError("No molecular system loaded in the viewer.")

        _, model, vectors = render_mode_vectors(
            view,
            molecular_system=molsys,
            selection=runtime.selection,
            cutoff=runtime.cutoff,
            mode_index=mode_index,
        )
        runtime.active_mode_index = mode_index
        return int(vectors.shape[0])

    def _build_state(self, runtime: Any, view: Any) -> dict:
        n_modes = self._get_n_modes(runtime, view)
        return {
            "mode_index": runtime.active_mode_index,
            "n_modes": n_modes,
            "model_kind": runtime.model_kind,
            "status": "idle",
            "error": None,
        }

    @staticmethod
    def _get_n_modes(runtime: Any, view: Any) -> int | None:
        cache_key = f"anm:{runtime.selection}:{runtime.cutoff}:0:MolSysMT"
        model = runtime.cached_models.get(cache_key)
        if model is None:
            return None
        try:
            modes = model.get_modes()
            return int(modes.shape[0])
        except Exception:
            return None
