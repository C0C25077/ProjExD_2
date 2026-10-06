import os
import random
import sys
import pygame as pg


WIDTH, HEIGHT = 1100, 650
DELTA = {
    pg.K_UP: (0, -5),
    pg.K_DOWN: (0, +5),
    pg.K_LEFT: (-5, 0),
    pg.K_RIGHT: (+5, 0),
}
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(rect: pg.Rect) -> tuple[bool, bool]:
    """
    引数：こうかとんまたは爆弾のRect
    戻り値：タプル（横方向判定結果，縦方向判定結果）
    画面内ならTrue／画面外ならFalse
    """
    yoko, tate = True, True
    if rect.left < 0 or WIDTH < rect.right:  # 横方向判定
        yoko = False
    if rect.top < 0 or HEIGHT < rect.bottom:  # 縦方向判定
        tate = False
    return yoko, tate


#演習１：ゲームオーバー画面
def show_game_over(screen: pg.Surface) -> None:
    """
    衝突時にゲームオーバー画面（暗転幕とGameOverテキスト）を表示する関数。
    引数：
        screen: 描画先の画面Surface
    """
    # 1. 画面全体を少し暗くする半透明の黒い膜を作成
    black_out = pg.Surface((WIDTH, HEIGHT))
    black_out.set_alpha(150)  # 透明度（0〜255）
    black_out.fill((0, 0, 0))
    screen.blit(black_out, (0, 0))

    # 2. 「GameOver」の文字を画面中央に表示
    font = pg.font.Font(None, 80)
    txt = font.render("GameOver", True, (255, 255, 255))
    txt_rect = txt.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(txt, txt_rect)

    # 3. 画面を更新し、2秒間静止してから終了
    pg.display.update()
    pg.time.wait(2000)
    

#演習２：時間経過によってボール拡大、加速
def calc_accel_bb(tmr: int, vx: int, vy: int) -> tuple[pg.Surface, float, float]:
    """
    経過時間 tmr に応じて拡大した爆弾 Surface と、加速された速度 (avx, avy) を返す関数。
    引数:
        tmr: 経過フレーム数
        vx, vy: 爆弾の元の移動速度（方向情報）
    戻り値:
        (拡大された爆弾 Surface, 加速後の x方向速度, 加速後の y方向速度)
    """
    # 拡大・加速の倍率計算（10段階、最大10倍まで）
    accel = min(10, 1 + tmr // 100)  # 100フレームごとに1倍ずつ上昇

    # 倍率に合わせて半径を計算（初期値 10px * accel）
    r = 10 * accel
    bb_img = pg.Surface((2 * r, 2 * r))
    pg.draw.circle(bb_img, (255, 0, 0), (r, r), r)  # 赤い円を描画
    bb_img.set_colorkey((0, 0, 0))  # 黒背景透過

    # 元の速度に向き(正負)を保ったまま倍率を掛ける
    avx = vx * accel
    avy = vy * accel

    return bb_img, avx, avy


#演習３：飛ぶ方向に従ってこうかとん画像を切り替える
def get_kk_img(sum_mv: tuple[int, int]) -> pg.Surface:
    """
    移動量 sum_mv (dx, dy) に応じて、適切な向きに回転・反転させたこうかとん画像を返す関数。
    引数：
        sum_mv: (dx, dy) の移動量タプル
    戻り値：
        回転・反転されたこうかとん Surface
    """
    # 左右反転と回転角の辞書定義 (左右反転フラグ, 回転角度)
    # 元画像（3.png）は「左向き」なので、それを基準に角度を設定
    kk_dict = {
        (0, 0): (False, 0),        # 静止時（左向き）
        (-5, 0): (False, 0),       # 左
        (-5, -5): (False, -45),    # 左上
        (0, -5): (True, 90),       # 上
        (+5, -5): (True, 45),      # 右上
        (+5, 0): (True, 0),        # 右
        (+5, +5): (True, -45),     # 右下
        (0, +5): (True, -90),      # 下
        (-5, +5): (False, 45),     # 左下
    }

    # デフォルト画像を設定しておき、辞書から該当する反転・角度を取得
    base_img = pg.image.load("fig/3.png")
    flip_h, angle = kk_dict.get(sum_mv, (False, 0))

    # 左右反転後に回転させて拡大率0.9で返す
    flipped_img = pg.transform.flip(base_img, flip_h, False)
    return pg.transform.rotozoom(flipped_img, angle, 0.9)


#演習4つ目：独自機能(スコアの描画)
def draw_score(screen: pg.Surface, tmr: int) -> None:
    """
    経過時間 tmr をもとにスコア（生存時間）を表示する関数。
    引数:
        screen: 描画先の画面Surface
        tmr: 経過フレーム数
    """
    font = pg.font.Font(None, 40)  # フォントオブジェクト作成（サイズ40）
    # tmr // 10 で適度な数字にする（10フレーム＝1スコア）
    score_txt = font.render(f"SCORE: {tmr // 10}", True, (0, 0, 0))
    screen.blit(score_txt, (20, 20))  # 画面の左上 (20, 20) に描画


def main():
    pg.display.set_caption("逃げろ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")    
    kk_img = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    kk_rct = kk_img.get_rect()
    kk_rct.center = 300, 200
    bb_img = pg.Surface((20, 20))  # 練習2：空のSurface
    pg.draw.circle(bb_img, (255, 0, 0), (10, 10), 10)  # 練習2：赤い爆弾
    bb_img.set_colorkey((0, 0, 0))  # 練習2：四隅の黒い部分を透過する
    bb_rct = bb_img.get_rect()
    bb_rct.centerx = random.randint(0, WIDTH)  # 横座標用の乱数
    bb_rct.centery = random.randint(0, HEIGHT)  # 縦座標用の乱数
    vx, vy = +5, +5  # 練習2：爆弾の初期速度
    clock = pg.time.Clock()
    tmr = 0
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT: 
                return
        screen.blit(bg_img, [0, 0]) 

        # 【追加機能1】衝突時の処理
        if kk_rct.colliderect(bb_rct):
            show_game_over(screen)  # 引数からkk_rctも不要になったため削除
            return

        key_lst = pg.key.get_pressed()
        sum_mv = [0, 0]
        for k, tpl in DELTA.items():
            if key_lst[k]:
                sum_mv[0] += tpl[0]  # 横方向移動量
                sum_mv[1] += tpl[1]  # 縦方向移動量
        kk_rct.move_ip(sum_mv)
        if check_bound(kk_rct) != (True, True):  # どこからしらはみ出てる
            kk_rct.move_ip(-sum_mv[0], -sum_mv[1])  # 先程の動きをキャンセルする
        screen.blit(kk_img, kk_rct)
        
        # 【追加機能3】現在の移動量 sum_mv に応じて画像を切り替えて描画
        kk_img = get_kk_img(tuple(sum_mv))
        screen.blit(kk_img, kk_rct)
        
        # 【追加機能2】爆弾の拡大・加速計算とRectのサイズ更新
        bb_img, avx, avy = calc_accel_bb(tmr, vx, vy)
        center = bb_rct.center
        bb_rct = bb_img.get_rect()
        bb_rct.center = center

        bb_rct.move_ip(vx, vy)  # 練習2：爆弾動く
        yoko, tate = check_bound(bb_rct)
        if not yoko:  # yoko == False
            vx *= -1
        if not tate:  # tate == False
            vy *= -1
        screen.blit(bb_img, bb_rct)  # 練習2：爆弾表示
        
        # 【独自機能（演習4）】スコアの描画
        draw_score(screen, tmr)
        
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()