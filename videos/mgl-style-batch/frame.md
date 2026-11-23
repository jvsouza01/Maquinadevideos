# Design System — Padrão MGL (Vertical 9:16 Mass Reels)

## Canvas & Estrutura
- **Resolução**: `1080x1920` (9:16 vertical, 30 fps)
- **Horizonte / Linha do Chão**: `y = 61.5%` (`1180px`), linha contínua de `4px` dividindo parede (superior) e chão (inferior).
- **Safe Zones**:
  - Topo: `y = 12%` até `36%` (`padding: 0 76px`) — Headline Zone
  - Palco Esquerdo: `x = 64px..560px`, `y = 35%..61%` — Props Geométricos / Ilustrações Vetoriais
  - Palco Direito: `x = 520px..1020px`, base nos pés apoiada em `y = 65.5%` — Mascote Chibi Sticker
  - Legenda Pill: centralizada em `y = 54.5%` (sobre o centro-baixo do palco), `2–3` palavras por bloco

## Paleta Tri-Tema (Alternância por Cena)
| Tema | Parede | Chão | Linha Horizonte | Texto Principal | Destaque Pill |
| --- | --- | --- | --- | --- | --- |
| `light` | `#EAEBEE` | `#D4D8E0` | `#14161D` | `#11131A` | `#D0EB2F` (texto `#11131A`) |
| `dark` | `#0F1017` | `#171821` | `#FFFFFF` | `#FFFFFF` | `#D0EB2F` (texto `#11131A`) |
| `lime` | `#D0EB2F` | `#B8D71A` | `#14161D` | `#11131A` | `#11131A` (texto `#FFFFFF`) |

## Tipografia
- **Display & Legendas**: `Sora` (700 / 800), `letter-spacing: -0.04em`, `line-height: 1.14`.
- **Headline**: `64px–74px`, alinhada à esquerda (ou em 2 colunas no modo `split`).
- **Legenda Pill**: fundo `#11131A` (`94%`), borda `2px solid rgba(255,255,255,0.16)`, `border-radius: 18px`, palavra ativa com pill `#D0EB2F` e texto `#11131A`.
