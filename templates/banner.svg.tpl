<svg xmlns="http://www.w3.org/2000/svg"
     width="{{TRIM_W}}mm" height="{{TRIM_H}}mm"
     viewBox="{{BLEED}} {{BLEED}} {{TRIM_W}} {{TRIM_H}}">
  <!--
    현수막 인쇄 마스터 · ministry-event-kit
    좌표 1 = 1mm · 도련 포함 {{FULL_W}} × {{FULL_H}} / 재단 {{TRIM_W}} × {{TRIM_H}}
    문구 안전영역: 좌우 {{SAFE_X}}mm · 상하 {{SAFE_Y}}mm 안쪽
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
      <stop offset="0"   stop-color="#ffffff"/>
      <stop offset=".32" stop-color="#f2effa"/>
      <stop offset=".68" stop-color="#d0c9e8"/>
      <stop offset="1"   stop-color="#b3a2cc"/>
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
  <rect x="0" y="0" width="{{FULL_W}}" height="{{FULL_H}}" fill="url(#grid)" mask="url(#gridMask)"/>

  <!-- 회로 장식: 타이틀 밴드를 비켜 위·아래 띠로 흐릅니다 -->
  <g transform="scale({{ART_SX}}, {{ART_SY}})">
    <g stroke="{{ACC2}}" stroke-width=".3" fill="none" opacity=".55" stroke-linecap="square">
      <path d="M0 16 H40 L50 11 H86"/>
      <path d="M0 72 H34 L44 78 H80"/>
      <path d="M0 45 H16 L22 38 H30"/>
      <path d="M400 16 H360 L350 11 H314"/>
      <path d="M400 72 H366 L356 78 H320"/>
      <path d="M400 45 H384 L378 38 H370"/>
    </g>
    <g fill="{{ACC1}}" opacity=".85">
      <rect x="86"    y="9.2"  width="3.6" height="3.6" rx=".6"/>
      <rect x="80"    y="76.2" width="3.6" height="3.6" rx=".6"/>
      <rect x="30"    y="36.2" width="3.6" height="3.6" rx=".6"/>
      <rect x="310.4" y="9.2"  width="3.6" height="3.6" rx=".6"/>
      <rect x="316.4" y="76.2" width="3.6" height="3.6" rx=".6"/>
      <rect x="366.4" y="36.2" width="3.6" height="3.6" rx=".6"/>
    </g>
  </g>

  <rect x="0" y="0" width="{{FULL_W}}" height="{{FULL_H}}" fill="url(#vignette)"/>
  <ellipse cx="{{CX}}" cy="{{HALO_CY}}" rx="{{HALO_RX}}" ry="{{HALO_RY}}" fill="url(#halo)"/>

  <!-- 주최 -->
  <g font-family="Pretendard, 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif" font-weight="700">
    <line x1="{{ORG_L1}}" y1="{{ORG_LY}}" x2="{{ORG_L2}}" y2="{{ORG_LY}}"
          stroke="{{ACC2}}" stroke-width="{{ORG_LW}}" opacity=".8"/>
    <line x1="{{ORG_R1}}" y1="{{ORG_LY}}" x2="{{ORG_R2}}" y2="{{ORG_LY}}"
          stroke="{{ACC2}}" stroke-width="{{ORG_LW}}" opacity=".8"/>
    <text x="{{CX}}" y="{{ORG_Y}}" font-size="{{ORG_SIZE}}" letter-spacing="{{ORG_LS}}"
          fill="{{ACC1}}" text-anchor="middle">{{ORG}}</text>
  </g>

  <!-- 메인 타이틀 — 입체감은 필터가 아니라 같은 글자를 겹쳐서 만듭니다 -->
  <g font-family="Pretendard, 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif"
     font-weight="900" font-size="{{T_SIZE}}" letter-spacing="{{T_LS}}" text-anchor="middle">
    <text x="{{TX}}" y="{{T_Y3}}" fill="{{SHADOW1}}">{{TITLE_PLAIN}}</text>
    <text x="{{TX}}" y="{{T_Y2}}" fill="{{SHADOW2}}">{{TITLE_PLAIN}}</text>
    <text x="{{TX}}" y="{{T_Y1}}" fill="url(#silver)"
          stroke="{{SHADOW2}}" stroke-width="{{T_STROKE}}" paint-order="stroke fill"
      >{{TITLE_HEAD}}<tspan fill="url(#accent)">{{TITLE_ACCENT}}</tspan></text>
  </g>

  <!-- 부제 · 날짜/장소 (있을 때만) -->
  {{SUBTITLE_BLOCK}}
  {{META_BLOCK}}
</svg>
