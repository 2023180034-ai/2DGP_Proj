보스 1 스프라이트 규격 (도트, 게임에서는 3배로 그림)

공통: 4방향 시트의 세로 줄은 pico2d bottom 기준 아래부터 down=0, left=1, right=2, up=3
      image.clip_draw(frame * W, dir * H, W, H, x, y, W * 3, H * 3)

파일                       칸 크기   프레임   방향   비고
boss1_idle.png             64x64     6        4      대기
boss1_walk.png             64x64     8        4      걷기
boss1_jump.png             128x128   13       4      점프 (발 위치 64,118)
boss1_land.png             128x128   12       4      착지 (3프레임 충격)
boss1_land_shadow.png      128x128   8        1      착지 예고 그림자 (반복)
boss1_shield_slam.png      128x128   12       4      방패 내려찍기 (6프레임 충격)
boss1_slam_warning.png     128x128   8        4      내려찍기 예고 (반복)
boss1_slam_eruption.png    128x128   10       4      땅 솟구침
boss1_charge_ready.png     128x128   4        4      돌진 준비
boss1_charge.png           128x128   6        4      돌진 (반복)
boss1_charge_warning.png   200x48    8        1      돌진 예고 화살표 (오른쪽 향함, 세로로 쌓음, 회전해서 사용)
boss1_shield_sweep.png     128x128   10       4      방패 휘두르기 (4~6프레임 판정)
boss1_sweep_warning.png    80x80     8        4      휘두르기 예고 (반복, 칸 가운데 = 보스 발보다 8px 위)

64칸과 128칸 시트는 발 위치가 다름: 64칸 발 (32, 59) / 128칸 발 (64, 118)
예고 이펙트 기준점:
  slam_warning, slam_eruption 범위 시작점 = 아래(64,4) 위(64,124) 오른쪽(4,64) 왼쪽(124,64)
