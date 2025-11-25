import os
import sys
import pygame as pg
import random
import time
import math

WIDTH, HEIGHT = 1100, 650
DELTA = {
    pg.K_UP: (0, -5),
    pg.K_DOWN: (0, +5),
    pg.K_LEFT: (-5, 0),
    pg.K_RIGHT: (+5, 0),
}
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def check_bound(rct: pg.Rect) -> tuple[bool, bool]:
    """
    引数：こうかとんRectまたは爆弾Rect
    戻り値：判定結果タプル（横方向，縦方向）
    画面内ならTrue，画面外ならFalse
    """
    yoko, tate = True, True
    if rct.left < 0 or WIDTH <rct.right:  # 横方向のはみ出しチェック
        yoko = False
    if rct.top < 0 or HEIGHT < rct.bottom:  # 縦方向のはみ出しチェック
        tate = False
    return yoko, tate

def game_over(screen:pg.Surface):
    overlay = pg.Surface((WIDTH, HEIGHT))
    overlay.fill((0, 0, 0))
    overlay.set_alpha(200) # 半透明
    font = pg.font.Font(None, 100)
    text = font.render("Game Over", True, (255, 255, 255))
    text_rect = text.get_rect(center=(WIDTH/2, HEIGHT/2))
    crying_kk_img = pg.transform.rotozoom(pg.image.load("fig/8.png"), 0, 2.0)
    left_kk_rect = crying_kk_img.get_rect()
    left_kk_rect.right = text_rect.left - 20
    left_kk_rect.centery = text_rect.centery + 10
    right_kk_rect = crying_kk_img.get_rect()
    right_kk_rect.left = text_rect.right + 20
    right_kk_rect.centery = text_rect.centery + 10
    screen.blit(overlay, [0, 0])
    screen.blit(text, text_rect)
    screen.blit(crying_kk_img, left_kk_rect)
    screen.blit(crying_kk_img, right_kk_rect)
    pg.display.update()
    time.sleep(5)

def prep_bombs() -> tuple[list, list]:
    bb_imgs = [] # 爆弾Surfaceのリスト
    for r in range(1, 11):
        bb_img = pg.Surface((20*r, 20*r))
        pg.draw.circle(bb_img, (255, 0, 0), (10*r, 10*r), 10*r)
        bb_img.set_colorkey((0, 0, 0)) # 黒い部分を透過
        bb_imgs.append(bb_img)
    bb_accs = [a for a in range(1, 11)]
    return bb_imgs, bb_accs

def get_kk_imgs() -> dict[tuple[int, int], pg.Surface]:
    """
    移動量タプルと対応する画像Surfaceの辞書を返す
    """
    kk_img0 = pg.image.load("fig/3.png") # 元画像
    base_img = pg.transform.rotozoom(kk_img0, 0, 0.9)
    kk_dict = {
        (0, 0): pg.transform.rotozoom(kk_img0, 0, 0.9), # 停止時
    }
    # 左右
    kk_dict[(-5, 0)] = pg.transform.rotozoom(kk_img0, 0, 0.9) # 右
    kk_dict[(+5, 0)] = pg.transform.flip(pg.transform.rotozoom(kk_img0, 0, 0.9), True, False) # 左

    kk_img_right = kk_dict[(+5, 0)]
    
    # 上下
    kk_dict[(0, -5)] = pg.transform.rotozoom(kk_img0, -90, 0.9) # 上
    kk_dict[(0, +5)] = pg.transform.rotozoom(kk_img0, 90, 0.9) # 下

    flipped_base_img = pg.transform.flip(base_img, True, False)
    
    # 斜め
    kk_dict[(-5, -5)] = pg.transform.rotozoom(kk_img0, 45, 0.9)
    kk_dict[(-5, +5)] = pg.transform.rotozoom(kk_img0, 135, 0.9)
    kk_dict[(+5, -5)] = pg.transform.rotozoom(kk_img0, -45, 0.9)
    kk_dict[(+5, +5)] = pg.transform.rotozoom(kk_img0, -135, 0.9)
    

    # 組み合わせた移動量（合計値）に対するキーも追加
    for y, x in [(-5, -5), (-5, +5), (+5, -5), (+5, +5)]:
        # 左右+上下
        if y != 0 and x != 0:
            kk_dict[(y, x)] = kk_dict[y, x] # 斜め移動
            
    # DELTAのキーを元にした合計移動量を網羅
    for y in [0, -5, +5]:
        for x in [0, -5, +5]:
            if (x, y) not in kk_dict:
                # 左右の合計、上下の合計
                if x != 0 and y == 0:
                    kk_dict[(x, y)] = kk_dict[(x, 0)]
                elif x == 0 and y != 0:
                    kk_dict[(x, y)] = kk_dict[(0, y)]
                elif x != 0 and y != 0:
                    # 斜めはすでに定義済みだが念のため
                    pass
    
    return kk_dict

def calc_orientation(org: pg.Rect, dst: pg.Rect, current_xy: tuple[float, float]) -> tuple[float, float]:
    """
    引数:
        org: 爆弾Rect (pg.Rect)
        dst: こうかとんRect (pg.Rect)
        current_xy: 現在の爆弾の速度ベクトル (vx, vy) (tuple[float, float])
    戻り値:
        移動すべき方向ベクトル (vx, vy) (tuple[float, float])
    """
    # 爆弾(org)からこうかとん(dst)へのベクトルを求める
    diff_x = dst.centerx - org.centerx
    diff_y = dst.centery - org.centery
    
    # 差ベクトルのノルム(長さ)
    norm = math.sqrt(diff_x**2 + diff_y**2)
    
    # ノルムが0、または200未満の場合の処理
    if norm == 0:
        return current_xy # 停止している場合は現在の速度を維持
    
    # 衝突寸前(距離300未満)の場合
    if norm < 300:
        # ゲームオーバーにならないように、現在の速度ベクトルを返す
        return current_xy
    
    # 正規化（ノルムを√50に調整）
    # √50は速度ベクトルのノルム(5, 5)の長さ(5√2)
    target_norm = math.sqrt(5**2 + 5**2) 
    
    vx = diff_x / norm * target_norm
    vy = diff_y / norm * target_norm
    
    # 小数点以下を無視すると水平・垂直に移動してしまうため、floatのまま返す
    return vx, vy

def main():
    pg.display.set_caption("逃げろ!こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")
    kk_imgs = get_kk_imgs() # こうかとんの画像を辞書として取得
    kk_img = kk_imgs[(0, 0)] # 初期画像は停止時のもの
    kk_img = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    kk_rct = kk_img.get_rect()
    kk_rct.center = 300, 200
    bb_imgs, bb_accs = prep_bombs() #機能2
    vx, vy = +5.0, +5.0# vx, vyを初期速度として定義し、浮動小数点数で保持
    bb_img = bb_imgs[0]
    bb_rct = bb_img.get_rect() # 爆弾Rect
    bb_rct.centerx = random.randint(0, WIDTH) # 爆弾横座標
    bb_rct.centery = random.randint(0, HEIGHT) # 爆弾縦座標
    vx, vy = +5, +5 # 爆弾の速度

    clock = pg.time.Clock()
    tmr = 0
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT: 
                return
        screen.blit(bg_img, [0, 0]) 
            
        if kk_rct.colliderect(bb_rct): # こうかとんと爆弾の衝突判定
            game_over(screen) # ゲームオーバー関数
            return # ゲームオーバー
        
        key_lst = pg.key.get_pressed()
        sum_mv = [0, 0]
        #if key_lst[pg.K_UP]:
        #    sum_mv[1] -= 5
        #if key_lst[pg.K_DOWN]:
        #    sum_mv[1] += 5
        #if key_lst[pg.K_LEFT]:
        #    sum_mv[0] -= 5
        #if key_lst[pg.K_RIGHT]:
        #    sum_mv[0] += 5
        for key,mv in DELTA.items():
            if key_lst[key]:
                sum_mv[0]+=mv[0]
                sum_mv[1]+=mv[1]

        mv_key = tuple(sum_mv) # 移動量のタプル (vx, vy)
        if mv_key in kk_imgs:
            kk_img = kk_imgs[mv_key]
        elif (mv_key[0], 0) in kk_imgs and mv_key[1] == 0:
             kk_img = kk_imgs[(mv_key[0], 0)]
        elif (0, mv_key[1]) in kk_imgs and mv_key[0] == 0:
             kk_img = kk_imgs[(0, mv_key[1])]
        else:
             kk_img = kk_imgs[(0, 0)]
    
        kk_rct.move_ip(sum_mv)
        if check_bound(kk_rct) != (True, True):  # 画面外なら
           kk_rct.move_ip(-sum_mv[0], -sum_mv[1])  # 移動をなかったことにする
        screen.blit(kk_img, kk_rct)
        level = min(tmr // 500, 9)
        current_bb_img = bb_imgs[level]
        bb_rct.width = current_bb_img.get_rect().width
        bb_rct.height = current_bb_img.get_rect().height
        vx, vy = calc_orientation(bb_rct, kk_rct, (vx, vy))
        acc = bb_accs[level]
        avx = vx * bb_accs[level]
        avy = vy * bb_accs[level]
        bb_rct.move_ip(avx, avy) # 爆弾移動は加速後の速度を使用
        yoko, tate = check_bound(bb_rct)
        #if not yoko:  # 横方向にはみ出ていたら
        #    vx *= -1
        #if not tate:  # 縦方向にはみ出ていたら
        #    vy *= -1

        current_bb_img = bb_imgs[level]

        screen.blit(current_bb_img, bb_rct)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
