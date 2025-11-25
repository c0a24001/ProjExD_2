import os
import sys
import pygame as pg
import random
import time

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

def main():
    pg.display.set_caption("逃げろ!こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")
    kk_img = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    kk_rct = kk_img.get_rect()
    kk_rct.center = 300, 200
    bb_imgs, bb_accs = prep_bombs() #機能2
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
        kk_rct.move_ip(sum_mv)
        if check_bound(kk_rct) != (True, True):  # 画面外なら
           kk_rct.move_ip(-sum_mv[0], -sum_mv[1])  # 移動をなかったことにする
        screen.blit(kk_img, kk_rct)
        level = min(tmr // 500, 9)
        avx = vx * bb_accs[level]
        avy = vy * bb_accs[level]
        bb_rct.move_ip(avx, avy) # 爆弾移動は加速後の速度を使用
        yoko, tate = check_bound(bb_rct)
        if not yoko:  # 横方向にはみ出ていたら
            vx *= -1
        if not tate:  # 縦方向にはみ出ていたら
            vy *= -1

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
