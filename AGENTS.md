# AGENTS.md — Guia Operacional para Agentes de IA (`Maquinadevideos`)

Este arquivo resume a arquitetura, invariantes técnicos obrigatórios, matriz de testes e receitas práticas para agentes de IA trabalharem neste repositório com segurança.

## 1. Mapa Rápido do Repositório

| Caminho | Responsabilidade |
| --- | --- |
| [`scripts/validate_workspace.py`](scripts/validate_workspace.py) | Validação global: audita mídias locais via `ffprobe`/`ebur128` (pula o que não existe em clone limpo), roda `unittest` e `test_preview_frames.js`. |
| [`tests/`](tests/) | Suíte `unittest` independente de mídias privadas (`test_workspace.py`, `test_mgl_v2.py`, `test_revenue_clean_pixar.py`). |
| [`videos/mgl-style-batch/`](videos/mgl-style-batch/) | Compilador JSON (`data/batch_scripts.json`) -> Edge-TTS `WordBoundary` + `cue_engine.py` + `mascot_rig.py` + `props_engine.py` -> HyperFrames `0.9.77`. |
| [`videos/revenue-clean-pixar/`](videos/revenue-clean-pixar/) | `build_audio_and_foley.py` (Edge-TTS + Foley WAV procedural) -> `build_scenes.py` (video-first `.mp4` com fallback `.jpg`) -> HyperFrames `0.9.77`. |
| [`videos/vistarumo-promo/`](videos/vistarumo-promo/) | Composição HyperFrames `0.9.26` declarativa (`1920x1080`, `22.7s`), com sub-composições em `compositions/frames/` e `BRIEF.md`/`frame.md`. |
| [`videos/whatsapp-reels/`](videos/whatsapp-reels/) | `build_audio.py` (grafo FFmpeg) + `index.html` (`window.chatTimeline.renderFrame(t)`) + `render_video.js` (Puppeteer PNG pipe -> FFmpeg) + `test_preview_frames.js`. |
| [`videos/relampeja-edit/`](videos/relampeja-edit/) | Pipeline Python puro (`common.py`, `generate_panels.py`, `generate_cards.py`, `build_subtitles.py`, `build_master_video.py`, `audit_final_video.py`). |

## 2. Invariantes Obrigatórios (Nunca Quebrar)

1. **Política de Mídias no Git**:
   - **NUNCA** force `git add -f` em `.mp4`, `.wav`, `.mp3`, `.ogg`, `.zip`, `renders/`, `.hyperframes/`, `capture/`, `validation_frames/`, `assets/clips/`, `assets/shots/`, `assets/audio/generated/` ou `scratch/`. Os vídeos produzidos e mídias brutas pertencem apenas ao ambiente local do usuário.
2. **Determinismo de Timeline (Seek-Safe)**:
   - Qualquer alteração em [`videos/whatsapp-reels/index.html`](videos/whatsapp-reels/index.html) **deve** manter `window.chatTimeline.renderFrame(t)` e `window.__timelines["whatsapp-reels"].seek(t)` puramente determinísticos (re-buscar qualquer `t` produz exatamente o mesmo `getState()` e DOM).
   - Em composições HyperFrames (`mgl-style-batch`, `revenue-clean-pixar`, `vistarumo-promo`), animações GSAP devem estar vinculadas à timeline pausada/controlada pelo HyperFrames (sem `requestAnimationFrame` livre ou timers assíncronos não determinísticos).
3. **Regras de Grafo FFmpeg (`build_audio.py` e `build_master_video.py`)**:
   - Todo stream de entrada reutilizado mais de uma vez em um `filter_complex` **deve** passar por `asplit=<N>` explícito antes de `adelay`/`sidechaincompress`.
   - Todo `amix` **deve** incluir `normalize=0`.
   - A mixagem master **deve** terminar com `loudnorm=I=-14:TP=-1.5:LRA=11` (exceto se o usuário solicitar alvo distinto).
4. **Portabilidade Cross-Platform**:
   - Não use caminhos hardcoded como `C:\...` sem fallback ou `env var` (`CHROME_PATH`, `get_font()`).
   - Em `subprocess.run(...)` com listas de argumentos, use `shell=False` e resolva binários com `shutil.which(...)`.
5. **Testes Independentes de Mídias Privadas**:
   - Novos testes em `tests/` **nunca** devem depender da existência de arquivos gitignored em `assets/` ou `scratch/`. Use `tempfile.TemporaryDirectory()` e `unittest.mock.patch`.

## 3. Matriz: "Alterei X -> Rode Y"

| Área Alterada | Comando Obrigatório de Verificação |
| --- | --- |
| `videos/mgl-style-batch/scripts/*.py` | `python -m unittest tests/test_mgl_v2.py -v` (e `npm --prefix videos/mgl-style-batch run check` se compilou HTML) |
| `videos/revenue-clean-pixar/scripts/*.py` | `python -m unittest tests/test_revenue_clean_pixar.py -v` |
| `videos/whatsapp-reels/build_audio.py` | `python -m unittest tests/test_workspace.py -v` |
| `videos/whatsapp-reels/index.html` ou `test_preview_frames.js` | `npm run test:whatsapp` |
| `videos/relampeja-edit/scripts/*.py` | `python -m unittest tests/test_workspace.py -v` |
| `videos/vistarumo-promo/**` | `npm run check:vistarumo` |
| Qualquer alteração global / pré-PR | `npm run test:python` e `python scripts/validate_workspace.py` |

## 4. Receitas Rápidas

- **Adicionar um novo vídeo no `mgl-style-batch`**:
  1. Adicione um objeto no array `"videos"` de [`videos/mgl-style-batch/data/batch_scripts.json`](videos/mgl-style-batch/data/batch_scripts.json) com `slug`, `title` e `scenes` (use poses de `mascot_rig.POSES` e props suportados por `props_engine.render_prop`).
  2. Rode `python videos/mgl-style-batch/scripts/build_batch.py <slug>`.
  3. Valide com `npm --prefix videos/mgl-style-batch run check` e renderize com `python videos/mgl-style-batch/scripts/render_batch.py <slug>`.
- **Adaptar `whatsapp-reels` para outro roteiro**:
  1. Atualize `SCRIPT` em [`videos/whatsapp-reels/index.html`](videos/whatsapp-reels/index.html) mantendo `OUTRO_START` e `DURATION`.
  2. Espelhe exatamente os mesmos timestamps de envio/recebimento/digitação em `SCRIPT_EVENTS` e `TYPING_WINDOWS` de [`videos/whatsapp-reels/build_audio.py`](videos/whatsapp-reels/build_audio.py).
  3. Atualize [`videos/whatsapp-reels/test_preview_frames.js`](videos/whatsapp-reels/test_preview_frames.js) e rode `npm run test:whatsapp`.
