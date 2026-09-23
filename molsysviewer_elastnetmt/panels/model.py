from __future__ import annotations

from typing import Any

from molsysviewer import AddonPanelWidget

from ..runtime import ensure_runtime, record_event

_ESM = """
export function render({ model, el }) {
  let state = {
    model_kind: "gnm",
    cutoff: "12 angstroms",
    status: "idle",
    error: null,
    n_nodes: null,
  };

  el.innerHTML = `
    <div class="enm-panel">
      <div class="enm-tabs" role="tablist">
        <button class="enm-tab enm-tab--active" data-kind="gnm" role="tab">GNM</button>
        <button class="enm-tab" data-kind="anm" role="tab">ANM</button>
      </div>
      <div class="enm-field">
        <label class="enm-label">Cutoff</label>
        <input class="enm-input" type="text" id="enm-cutoff" />
      </div>
      <button class="enm-btn enm-btn--primary" id="enm-compute">Compute</button>
      <div class="enm-status" id="enm-status"></div>
    </div>
  `;

  const tabBtns = el.querySelectorAll(".enm-tab");
  const cutoffInput = el.querySelector("#enm-cutoff");
  const computeBtn = el.querySelector("#enm-compute");
  const statusEl = el.querySelector("#enm-status");

  function applyState(s) {
    state = { ...state, ...s };

    tabBtns.forEach((btn) => {
      btn.classList.toggle("enm-tab--active", btn.dataset.kind === state.model_kind);
    });

    if (document.activeElement !== cutoffInput) {
      cutoffInput.value = state.cutoff;
    }

    computeBtn.disabled = state.status === "computing";
    computeBtn.textContent = state.status === "computing" ? "Computing…" : "Compute";

    if (state.status === "done" && state.n_nodes !== null) {
      statusEl.textContent = `Done — ${state.n_nodes} nodes`;
      statusEl.className = "enm-status enm-status--ok";
    } else if (state.status === "error" && state.error) {
      statusEl.textContent = `Error: ${state.error}`;
      statusEl.className = "enm-status enm-status--error";
    } else if (state.status === "computing") {
      statusEl.textContent = "Computing…";
      statusEl.className = "enm-status enm-status--busy";
    } else {
      statusEl.textContent = "";
      statusEl.className = "enm-status";
    }
  }

  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      model.send({ type: "action", id: "set_model_kind", payload: { model_kind: btn.dataset.kind } });
    });
  });

  cutoffInput.addEventListener("change", () => {
    model.send({ type: "action", id: "set_cutoff", payload: { cutoff: cutoffInput.value.trim() } });
  });

  computeBtn.addEventListener("click", () => {
    model.send({ type: "action", id: "compute", payload: {} });
  });

  model.on("msg:custom", (msg) => {
    if (msg?.type === "state") applyState(msg.state);
    else if (msg?.type === "context") {
      /* context received — nothing to do for model panel */
    }
  });

  model.send({ type: "query", id: "viewer.context" });

  applyState(state);
}
"""

_CSS = """
.enm-panel {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px;
  font-size: 13px;
  font-family: sans-serif;
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
.enm-input {
  padding: 4px 6px;
  border: 1px solid #555;
  background: transparent;
  color: inherit;
  border-radius: 4px;
  font-size: 13px;
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


class ElastNetMTModelPanel(AddonPanelWidget):
    _esm: str = _ESM
    _css: str = _CSS

    def on_mount(self, view: Any) -> None:
        runtime = ensure_runtime(view)
        self.push_state(self._build_state(runtime))

    def handle_action(self, view: Any, action_id: str, payload: dict) -> None:
        runtime = ensure_runtime(view)

        if action_id == "set_model_kind":
            kind = payload.get("model_kind", runtime.model_kind)
            if kind in ("gnm", "anm"):
                runtime.model_kind = kind
                record_event(view, "panel_set_model_kind", model_kind=kind)
                self.push_state(self._build_state(runtime))

        elif action_id == "set_cutoff":
            cutoff = payload.get("cutoff", runtime.cutoff)
            if isinstance(cutoff, str) and cutoff.strip():
                runtime.cutoff = cutoff.strip()
                record_event(view, "panel_set_cutoff", cutoff=runtime.cutoff)
                self.push_state(self._build_state(runtime))

        elif action_id == "compute":
            self.push_state({**self._build_state(runtime), "status": "computing"})
            try:
                n_nodes = self._run_compute(view, runtime)
                record_event(
                    view,
                    "panel_compute",
                    model_kind=runtime.model_kind,
                    n_nodes=n_nodes,
                )
                self.push_state(
                    {**self._build_state(runtime), "status": "done", "n_nodes": n_nodes}
                )
            except Exception as exc:
                self.push_state(
                    {**self._build_state(runtime), "status": "error", "error": str(exc)}
                )

    def _run_compute(self, view: Any, runtime: Any) -> int:
        from ..adapters.contacts import get_or_build_contact_model
        from ..adapters.modes import get_or_build_anm_model

        molsys = getattr(view, "_molsys", None) or getattr(
            view, "molecular_system", None
        )
        if molsys is None:
            raise RuntimeError("No molecular system loaded in the viewer.")

        if runtime.model_kind == "gnm":
            model = get_or_build_contact_model(
                view,
                molecular_system=molsys,
                selection=runtime.selection,
                cutoff=runtime.cutoff,
            )
        else:
            model = get_or_build_anm_model(
                view,
                molecular_system=molsys,
                selection=runtime.selection,
                cutoff=runtime.cutoff,
            )

        atom_indices = getattr(model, "atom_indices", None)
        return len(atom_indices) if atom_indices is not None else 0

    @staticmethod
    def _build_state(runtime: Any) -> dict:
        return {
            "model_kind": runtime.model_kind,
            "cutoff": runtime.cutoff,
            "status": "idle",
            "error": None,
            "n_nodes": None,
        }
