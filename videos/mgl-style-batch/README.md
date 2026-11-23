# MGL-Style Vertical Batch Video Generator — Motor v2 (`1080x1920`)

Pipeline parametrizado **HyperFrames (`0.9.77`) + Edge-TTS + GSAP** com **sincronia palavra-gatilho (`Word-Cue Engine`)**, **rigging 2.5D articulado** e **artes componíveis** para produção em massa no padrão `videomgl`.

## Arquitetura do Motor v2
- **`scripts/cue_engine.py`**: Resolve `cue_word` diretamente nos timestamps `WordBoundary` do `edge-tts`, gera envelopes de lip-sync/head-nodding e agrupa legendas pill sem sobreposição temporal.
- **`scripts/mascot_rig.py`**: Rig 2.5D multi-camadas (`.mascot-shadow`, `.mascot-body-rig`, `.mascot-head-rig`, `.mascot-eyelids`, `.mascot-mouth`, `.mascot-arm-l`, `.mascot-arm-r`) com *squash & stretch*, piscada automática, *lip-sync*, gestos nos cues e trocas de pose intra-cena (`pose_cues`). Aceita `<pose>.png` transparentes em `assets/mascot/` como override.
- **`scripts/props_engine.py`**: Artes componíveis via JSON com entrada *step-by-step* no timestamp da palavra (`split-wheel-checklist`, `comparison_doors`, `versus_grid`, `door-crowd`, `cards_stack`, `offer_showcase`, `flow_steps` com `stroke-dashoffset`, `metrics_board` e `bar_chart` com *count-up* animado).
- **`scripts/build_batch.py`**: Compila `data/batch_scripts.json` gerando cortina vertical (`clip-path`), câmera virtual com *punch-in*/*shake*, parallax 3 camadas, *highlight sweep* (`scaleX: 0 -> 1`) e mixagem de áudio sem sobreposição de trilhas.

## Uso Rápido
```bash
npm run build        # gera TTS + WordBoundary + composições v2
npm run check        # valida lint, layout, safe-zones, contraste e craft
npm run render       # renderiza o 1º vídeo (renders/01-ranking-ia-validados.mp4)
python scripts/render_batch.py  # renderiza todo o lote
```
