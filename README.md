# Bioglow Logo Animation

`Picture3.png` 원본 로고를 픽셀 단위로 분석해서 잎/점/회로선/뿌리 8개 레이어로 분리하고, 흔들림+글로우 펄스 애니메이션으로 만든 GIF.

## 파일

- `Picture3.png` — 원본 로고
- `layer_*.png` — 원본에서 분리한 레이어 (leaf_base, dot1-4, tendril1, root1-2, background)
- `bioglow_animated.gif` — 최종 애니메이션 (700×700, 루프)
- `build_layers2.py` — 원본 PNG → 레이어 분리 (connected-component 분석, 재조합 시 원본과 diff 0 검증)
- `animate.py` — 레이어 → 애니메이션 GIF 생성

## 실행

```
pip install pillow opencv-python-headless numpy
python build_layers2.py   # Picture3.png -> layer_*.png
python animate.py         # layer_*.png -> bioglow_animated.gif
```
