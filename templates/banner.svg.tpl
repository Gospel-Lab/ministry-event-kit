<svg xmlns="http://www.w3.org/2000/svg"
     width="{{TRIM_W}}mm" height="{{TRIM_H}}mm"
     viewBox="{{BLEED}} {{BLEED}} {{TRIM_W}} {{TRIM_H}}">
  <!--
    현수막 인쇄 마스터 · ministry-event-kit
    좌표 1 = 1mm · 도련 포함 {{FULL_W}} × {{FULL_H}} / 재단 {{TRIM_W}} × {{TRIM_H}}
    문구 안전영역: 좌우 {{SAFE_X}}mm · 상하 {{SAFE_Y}}mm 안쪽
    배치 {{LAYOUT}} · 배경무늬 {{MOTIF_NAME}}

    ※ 색은 여기에 적지 않습니다. 전부 scripts/theme.py 에서 옵니다.
    ※ SVG 필터를 쓰지 않습니다. 필터는 PDF 변환 때 저해상 래스터로 떨어집니다.
  -->
  <defs>
    <!-- 배경 — 색상각 275~285°(자보라)를 유지해야 CMYK에서 남색으로 빠지지 않습니다 -->
    <linearGradient id="base" x1="0" y1="0" x2="1" y2=".55">
      <stop offset="0"   stop-color="{{BG1}}"/>
      <stop offset=".40" stop-color="{{BG2}}"/>
      <stop offset=".70" stop-color="{{BG3}}"/>
      <stop offset="1"   stop-color="{{BG4}}"/>
    </linearGradient>
    <radialGradient id="glow" cx=".5" cy="1.28" r=".72">
      <stop offset="0" stop-color="{{GLOW}}" stop-opacity=".34"/>
      <stop offset="1" stop-color="{{GLOW}}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="vignette" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0"   stop-color="#000000" stop-opacity=".24"/>
      <stop offset=".32" stop-color="#000000" stop-opacity="0"/>
      <stop offset=".60" stop-color="#000000" stop-opacity="0"/>
      <stop offset="1"   stop-color="#000000" stop-opacity=".38"/>
    </linearGradient>
    <radialGradient id="halo" cx=".5" cy=".5" r=".5">
      <stop offset="0"   stop-color="{{HALO}}" stop-opacity=".40"/>
      <stop offset=".52" stop-color="{{HALO}}" stop-opacity=".18"/>
      <stop offset="1"   stop-color="{{HALO}}" stop-opacity="0"/>
    </radialGradient>

    <pattern id="grid" width="{{GRID}}" height="{{GRID}}" patternUnits="userSpaceOnUse">
      <path d="M{{GRID}} 0 L0 0 0 {{GRID}}" fill="none"
            stroke="{{GRIDC}}" stroke-width="{{GRIDW}}" opacity=".42"/>
    </pattern>
    <pattern id="dots" width="{{GRID}}" height="{{GRID}}" patternUnits="userSpaceOnUse">
      <circle cx="{{DOT_C}}" cy="{{DOT_C}}" r="{{DOT_R}}" fill="{{GRIDC}}" opacity=".34"/>
    </pattern>
    <linearGradient id="gridFade" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0"   stop-color="#ffffff" stop-opacity=".85"/>
      <stop offset=".37" stop-color="#ffffff" stop-opacity="0"/>
      <stop offset=".63" stop-color="#ffffff" stop-opacity="0"/>
      <stop offset="1"   stop-color="#ffffff" stop-opacity=".85"/>
    </linearGradient>
    <mask id="gridMask">
      <rect x="0" y="0" width="{{FULL_W}}" height="{{FULL_H}}" fill="url(#gridFade)"/>
    </mask>

    <linearGradient id="silver" x1="0" y1="{{T_TOP}}" x2="0" y2="{{T_BOT}}" gradientUnits="userSpaceOnUse">
      <stop offset="0"   stop-color="{{HI1}}"/>
      <stop offset=".32" stop-color="{{HI2}}"/>
      <stop offset=".68" stop-color="{{HI3}}"/>
      <stop offset="1"   stop-color="{{HI4}}"/>
    </linearGradient>
    <linearGradient id="accent" x1="0" y1="{{T_TOP}}" x2="0" y2="{{T_BOT}}" gradientUnits="userSpaceOnUse">
      <stop offset="0"   stop-color="{{ACC1}}"/>
      <stop offset=".46" stop-color="{{ACC2}}"/>
      <stop offset="1"   stop-color="{{ACC3}}"/>
    </linearGradient>
  </defs>

  <!-- 배경: 도련 끝까지 채웁니다 -->
  <rect x="0" y="0" width="{{FULL_W}}" height="{{FULL_H}}" fill="url(#base)"/>
  <rect x="0" y="0" width="{{FULL_W}}" height="{{FULL_H}}" fill="url(#glow)"/>
  {{GRID_LAYER}}

  <!-- 배경 무늬 -->
  {{MOTIF}}

  <rect x="0" y="0" width="{{FULL_W}}" height="{{FULL_H}}" fill="url(#vignette)"/>
  <ellipse cx="{{HALO_CX}}" cy="{{HALO_CY}}" rx="{{HALO_RX}}" ry="{{HALO_RY}}" fill="url(#halo)"/>

  <!-- 문구 — 배치는 scripts/make_banner.py 가 만듭니다 -->
  {{CONTENT}}
</svg>
