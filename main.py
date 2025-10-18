import tkinter as tk
import pandas as pd
import matplotlib.pyplot as plt
import os
import configparser


class QuadrantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("4象限クリックツール")
        self.width, self.height = 600, 600
        self.center = (self.width / 2, self.height / 2)
        self.read_config("config.ini")  # configファイルの読み込み

        # メインフレーム
        main_frame = tk.Frame(root)
        main_frame.pack(padx=10, pady=10)

        # Canvas
        self.canvas = tk.Canvas(
            main_frame, width=self.width, height=self.height, bg="white"
        )
        self.canvas.grid(row=0, column=0)

        # 十字線（破線・双方向矢印）
        self.hline = self.canvas.create_line(
            0,
            self.center[1],
            self.width,
            self.center[1],
            fill="black",
            width=2,
            arrow=tk.BOTH,
            dash=(5, 3),
        )
        self.vline = self.canvas.create_line(
            self.center[0],
            0,
            self.center[0],
            self.height,
            fill="black",
            width=2,
            arrow=tk.BOTH,
            dash=(5, 3),
        )

        # 軸ラベル
        label_font = ("Arial", 12, "bold")

        # X軸ラベル
        self.canvas.create_text(
            self.width - 20, self.center[1] - 15, text=self.label_right, font=label_font
        )
        self.canvas.create_text(
            20, self.center[1] - 15, text=self.label_left, font=label_font
        )

        # Y軸ラベル
        self.canvas.create_text(
            self.center[0] + 20, 20, text=self.label_up, font=label_font
        )
        self.canvas.create_text(
            self.center[0] + 25, self.height - 20, text=self.label_down, font=label_font
        )

        # 操作説明枠
        instr_frame = tk.LabelFrame(main_frame, text="凡例・操作方法", padx=10, pady=10)

        # 赤/青の凡例
        legend_frame = tk.Frame(instr_frame)
        legend_frame.pack(anchor="w", pady=(0, 5))

        # 赤丸
        red_canvas = tk.Canvas(
            legend_frame, width=15, height=15, bg="white", highlightthickness=0
        )
        red_canvas.create_oval(3, 3, 11, 11, fill="red")  # 小さく
        red_canvas.pack(side="left")
        tk.Label(legend_frame, text=": before", font=("Arial", 10)).pack(
            side="left", padx=(2, 10)
        )

        # 青丸
        blue_canvas = tk.Canvas(
            legend_frame, width=15, height=15, bg="white", highlightthickness=0
        )
        blue_canvas.create_oval(3, 3, 11, 11, fill="blue")  # 小さく
        blue_canvas.pack(side="left")
        tk.Label(legend_frame, text=": after", font=("Arial", 10)).pack(
            side="left", padx=(2, 10)
        )

        instructions = (
            "Step 1. 左クリック（1 回目: before, 2 回目: after）\n"
            "Step 2. 右クリック+ドラッグ: 修正\n"
            "Step 3. 保存ボタン\n"
        )
        instr_label = tk.Label(
            instr_frame, text=instructions, justify="left", font=("Arial", 10)
        )
        instr_label.pack(anchor="w")
        instr_frame.grid(row=0, column=1, sticky="nw", padx=10, pady=10)

        # 内部データ
        self.points = []
        self.current_id = 1
        self.current_type = "before"
        self.drag_data = {"item": None, "offset": (0, 0)}

        # イベント
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Button-3>", self.on_drag_start)
        self.canvas.bind("<B3-Motion>", self.on_drag_motion)
        self.canvas.bind("<ButtonRelease-3>", self.on_drag_release)

        # CSV初期化
        if not os.path.exists(f"out/{self.item}.csv"):
            pd.DataFrame(columns=["id", "type", "x", "y"]).to_csv(
                f"out/{self.item}.csv", index=False
            )
        else:
            self.load_csv()

        # 保存ボタン
        self.save_button = tk.Button(
            root,
            text=f"保存 ( ID={self.current_id} )",
            font=("Arial", 12, "bold"),
            bg="green",
            fg="white",
            activebackground="darkgreen",
            padx=10,
            pady=5,
            command=self.save_and_fix,
        )
        self.save_button.pack(pady=10)

    def read_config(self, filename):
        config = configparser.ConfigParser()
        config.read(filename)
        self.item = str(config["Item"]["name"])
        self.label_up = str(config["Axis"]["up"])
        self.label_down = str(config["Axis"]["down"])
        self.label_left = str(config["Axis"]["left"])
        self.label_right = str(config["Axis"]["right"])
        self.label_axis_x = str(config["Axis"]["label_x"])
        self.label_axis_y = str(config["Axis"]["label_y"])

    # 座標変換
    def canvas_to_math(self, x, y):
        return x - self.center[0], self.center[1] - y

    def math_to_canvas(self, mx, my):
        return mx + self.center[0], self.center[1] - my

    # 点クリック追加
    def on_click(self, event):
        if event.widget.find_withtag("current") in ([self.hline], [self.vline]):
            return

        if self.is_current_id_fixed():
            print("このidはすでに固定されています。新しい入力を開始してください。")
            return

        if self.has_type_for_current_id(self.current_type):
            print(f"{self.current_type} はすでに入力済みです。")
            self.current_type = "after" if self.current_type == "before" else "before"
            return

        x, y = event.x, event.y
        mx, my = self.canvas_to_math(x, y)
        color = "red" if self.current_type == "before" else "blue"

        # 小さい点に変更
        r = 3
        item = self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=color)
        self.points.append((self.current_id, self.current_type, mx, my, item, False))
        self.save_to_csv()

        self.current_type = "after" if self.current_type == "before" else "before"

    # ドラッグ系
    def on_drag_start(self, event):
        item = self.canvas.find_closest(event.x, event.y)
        if not item or item[0] in (self.hline, self.vline):
            return
        for pid, ptype, x, y, it, fixed in self.points:
            if it == item[0] and fixed:
                return
        self.drag_data["item"] = item[0]

    def on_drag_motion(self, event):
        if self.drag_data["item"] is None:
            return
        item = self.drag_data["item"]
        x, y = event.x, event.y
        r = 3
        self.canvas.coords(item, x - r, y - r, x + r, y + r)

    def on_drag_release(self, event):
        if self.drag_data["item"] is None:
            return
        item = self.drag_data["item"]
        x, y = (self.canvas.coords(item)[0] + self.canvas.coords(item)[2]) / 2, (
            self.canvas.coords(item)[1] + self.canvas.coords(item)[3]
        ) / 2
        mx, my = self.canvas_to_math(x, y)
        for i, (pid, ptype, _, _, it, fixed) in enumerate(self.points):
            if it == item:
                self.points[i] = (pid, ptype, mx, my, item, fixed)
                break
        self.drag_data = {"item": None, "offset": (0, 0)}
        self.save_to_csv()

    def is_current_id_fixed(self):
        return any(
            pid == self.current_id and fixed for pid, _, _, _, _, fixed in self.points
        )

    def has_type_for_current_id(self, type_name):
        return any(
            pid == self.current_id and ptype == type_name
            for pid, ptype, _, _, _, _ in self.points
        )

    def save_and_fix(self):
        if not any(p[0] == self.current_id for p in self.points):
            print("このidの点がありません。")
            return

        for i, (pid, ptype, x, y, item, fixed) in enumerate(self.points):
            if pid == self.current_id:
                color = "#ff9999" if ptype == "before" else "#9999ff"
                self.canvas.itemconfig(item, fill=color)
                self.points[i] = (pid, ptype, x, y, item, True)

        print(f"id={self.current_id} のデータを固定しました。")
        self.save_to_csv()
        self.visualize_scatter_plot()

        # 次のIDに更新
        self.current_id += 1
        self.current_type = "before"
        self.save_button.config(text=f"保存 ( ID={self.current_id} )")
        print(f"新しいid={self.current_id} の入力を開始します。")

    # CSV保存
    def save_to_csv(self):
        df = pd.DataFrame(
            [(pid, ptype, x, y) for pid, ptype, x, y, _, _ in self.points],
            columns=["id", "type", "x", "y"],
        )
        df.to_csv(f"out/{self.item}.csv", index=False)

    # CSV読み込み
    def load_csv(self):
        df = pd.read_csv(f"out/{self.item}.csv")
        for _, row in df.iterrows():
            x_canvas, y_canvas = self.math_to_canvas(row["x"], row["y"])
            color = "#ff9999" if row["type"] == "before" else "#9999ff"
            r = 3
            item = self.canvas.create_oval(
                x_canvas - r, y_canvas - r, x_canvas + r, y_canvas + r, fill=color
            )
            self.points.append(
                (
                    int(row["id"]),
                    row["type"],
                    float(row["x"]),
                    float(row["y"]),
                    item,
                    True,
                )
            )
            self.current_id = max(self.current_id, int(row["id"]) + 1)

    # PNG出力
    def visualize_scatter_plot(self):
        df = pd.read_csv(f"out/{self.item}.csv")
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.set_xlim(-300, 300)
        ax.set_ylim(-300, 300)
        ax.set_aspect("equal", adjustable="box")  # ← これで縦横比1:1

        # 横軸
        ax.annotate(
            "",
            xy=(300, 0),
            xytext=(-300, 0),
            arrowprops=dict(
                arrowstyle="<->", color="black", linestyle="--", linewidth=0.8
            ),
        )

        # 縦軸
        ax.annotate(
            "",
            xy=(0, 300),
            xytext=(0, -300),
            arrowprops=dict(
                arrowstyle="<->", color="black", linestyle="--", linewidth=0.8
            ),
        )

        before = df[df["type"] == "before"]
        after = df[df["type"] == "after"]
        ax.scatter(before["x"], before["y"], s=10, color="red", label="before")
        ax.scatter(after["x"], after["y"], s=10, color="blue", label="after")

        # 軸ラベル・タイトル
        ax.set_title(self.item, fontsize=14, fontweight="bold", pad=10)
        ax.set_xlabel(self.label_axis_x, fontsize=12)
        ax.set_ylabel(self.label_axis_y, fontsize=12)

        # 枠線とメモリを消す
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

        ax.legend()
        plt.savefig(f"out/{self.item}.png", bbox_inches="tight", pad_inches=0.2)
        plt.close(fig)
        print("PNGを保存しました。")


if __name__ == "__main__":
    root = tk.Tk()
    app = QuadrantApp(root)
    root.mainloop()
