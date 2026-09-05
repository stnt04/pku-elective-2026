#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# gui.py —— PKU Auto-Elective 可视化配置窗口（CustomTkinter）
# 用法：python gui.py
import os, sys, configparser, subprocess, threading, shutil
import tkinter as tk
from tkinter import messagebox

from ensure_deps import ensure   # 先自动检查/安装缺失依赖
ensure()

import customtkinter as ctk

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(BASE, 'config.ini')

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
# 去掉 CTkTabview 标签头那条默认 3px 的描边（类属性写死，需在创建前改）
ctk.CTkTabview._segmented_button_border_width = 0


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PKU Auto-Elective 配置工具")
        self.geometry("800x600")
        self.minsize(720, 520)
        self.cfg = configparser.ConfigParser(allow_no_value=True)
        if os.path.exists(CONFIG):
            self.cfg.read(CONFIG, encoding='utf-8')
        self._courses = []      # list of dict {id,name,klass,school}
        self._row_widgets = {}  # course row index -> {widgets}
        self.param_entries = {} # key -> (entry, type, default)
        self.bool_cb = {}       # key -> checkbox
        self.sel_course = ctk.IntVar(value=0)
        self.proc = None       # 后台选课任务进程
        self.log_enabled = ctk.BooleanVar(value=True)   # 记录日志开关
        self._load_courses_from_file()
        self._build_ui()
        self._fill_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------- helpers ----------
    def _get(self, sec, key, default=''):
        try:
            return self.cfg.get(sec, key, fallback=default)
        except Exception:
            return default

    def _load_courses_from_file(self):
        self._courses = []
        for sec in self.cfg.sections():
            if sec.startswith('course:'):
                self._courses.append({
                    'id': sec.split(':', 1)[1],
                    'name': self.cfg.get(sec, 'name', fallback=''),
                    'klass': self.cfg.get(sec, 'class', fallback=''),
                    'school': self.cfg.get(sec, 'school', fallback=''),
                })

    # ---------- UI ----------
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        tab = ctk.CTkTabview(self, width=760, height=470,
                             corner_radius=24, border_width=0)
        tab.grid(row=0, column=0, padx=12, pady=(6, 0), sticky='nsew')
        try:  # 去边框线 + 标签头底色与内容一致（消除色带/对比线）
            tab._segmented_button.configure(
                border_width=0,
                fg_color=self._apply_appearance_mode(tab.cget('fg_color')))
            tab._configure_segmented_button_background_corners()
        except Exception:
            pass
        tab.add("登录信息"); tab.add("目标课程"); tab.add("运行参数"); tab.add("高级")

        # --- 登录信息 ---
        f = tab.tab("登录信息")
        f.grid_columnconfigure(1, weight=1)
        rows = [
            ("学号", "student_id", "text"),
            ("密码", "password", "password"),
        ]
        for i, (label, key, kind) in enumerate(rows):
            ctk.CTkLabel(f, text=label, anchor="w").grid(row=i, column=0, padx=14, pady=12, sticky='w')
            ent = ctk.CTkEntry(f, width=280)
            ent.grid(row=i, column=1, sticky='we')
            if kind == "password":
                ent.configure(show="*")
            setattr(self, 'ent_' + key, ent)
        ctk.CTkLabel(f, text="双学位账号", anchor="w").grid(row=2, column=0, padx=14, pady=12, sticky='w')
        self.cmb_dual = ctk.CTkOptionMenu(f, values=["false", "true"], width=140)
        self.cmb_dual.grid(row=2, column=1, sticky='w')
        ctk.CTkLabel(f, text="登录身份 (identity)", anchor="w").grid(row=3, column=0, padx=14, pady=12, sticky='w')
        self.cmb_ident = ctk.CTkOptionMenu(f, values=["bfx", "bzx"], width=140)
        self.cmb_ident.grid(row=3, column=1, sticky='w')
        ctk.CTkLabel(f, text="提示：学号/密码即 IAAA 统一认证账号；双学位账号需把 dual_degree 设为 true。",
                     text_color="gray60", anchor="w").grid(row=4, column=0, columnspan=2, padx=14, pady=12, sticky='w')

        # --- 目标课程 ---
        fc = tab.tab("目标课程")
        fc.grid_columnconfigure(0, weight=1)
        fc.grid_rowconfigure(1, weight=1)
        head = ctk.CTkFrame(fc)
        head.grid(row=0, column=0, sticky='ew', padx=8, pady=6)
        ctk.CTkLabel(head, text="课程名", width=240).grid(row=0, column=0, padx=6)
        ctk.CTkLabel(head, text="班号", width=80).grid(row=0, column=1, padx=6)
        ctk.CTkLabel(head, text="开课单位", width=180).grid(row=0, column=2, padx=6)
        ctk.CTkLabel(head, text="操作", width=140).grid(row=0, column=3, padx=6)
        self.course_frame = ctk.CTkScrollableFrame(fc, height=330)
        self.course_frame.grid(row=1, column=0, sticky='nsew', padx=8, pady=4)
        ctk.CTkLabel(fc, text="顺序即优先级：越靠上越先提交抢占。", text_color="gray60",
                     anchor="w").grid(row=2, column=0, sticky='w', padx=14, pady=4)
        bar = ctk.CTkFrame(fc); bar.grid(row=3, column=0, sticky='ew', padx=8, pady=6)
        ctk.CTkButton(bar, text="＋ 添加课程", width=110, command=self.add_course).grid(row=0, column=0, padx=6)
        ctk.CTkButton(bar, text="上移", width=80, command=lambda: self.move_course(-1)).grid(row=0, column=1, padx=6)
        ctk.CTkButton(bar, text="下移", width=80, command=lambda: self.move_course(1)).grid(row=0, column=2, padx=6)
        ctk.CTkButton(bar, text="删除选中", width=90, command=self.remove_course).grid(row=0, column=3, padx=6)
        self.sel_course = ctk.IntVar(value=0)

        # --- 运行参数 ---
        fr = tab.tab("运行参数")
        fr.grid_columnconfigure(0, weight=1)
        fr.grid_columnconfigure(2, weight=1)
        numeric = [
            ("刷新间隔 refresh_interval (s)", "refresh_interval", "float", "4"),
            ("随机偏移 random_deviation", "random_deviation", "float", "0.3"),
            ("补退选页 supply_cancel_page", "supply_cancel_page", "int", "1"),
            ("IAAA 超时 iaaa_client_timeout (s)", "iaaa_client_timeout", "float", "30"),
            ("选课超时 elective_client_timeout (s)", "elective_client_timeout", "float", "60"),
            ("连接池大小 elective_client_pool_size", "elective_client_pool_size", "int", "2"),
            ("会话存活 elective_client_max_life (s)", "elective_client_max_life", "int", "600"),
            ("登录循环间隔 login_loop_interval (s)", "login_loop_interval", "float", "2"),
        ]
        self.param_entries = {}
        for i, (label, key, typ, dflt) in enumerate(numeric):
            col, row = (0, i) if i < 4 else (2, i - 4)
            ctk.CTkLabel(fr, text=label, anchor="w", width=280).grid(row=row, column=col, padx=16, pady=10, sticky='w')
            ent = ctk.CTkEntry(fr, width=120)
            ent.grid(row=row, column=col + 1, padx=8, pady=10, sticky='w')
            self.param_entries[key] = (ent, typ, dflt)
        bools = [
            ("打印互斥规则 print_mutex_rules", "print_mutex_rules"),
            ("打印请求细节 debug_print_request", "debug_print_request"),
            ("记录请求日志 debug_dump_request", "debug_dump_request"),
        ]
        for i, (label, key) in enumerate(bools):
            r = 4 + i
            ctk.CTkLabel(fr, text=label, anchor="w", width=280).grid(row=r, column=2, padx=16, pady=10, sticky='w')
            cb = ctk.CTkCheckBox(fr, text="启用", width=90)
            cb.grid(row=r, column=3, padx=8, pady=10, sticky='w')
            self.bool_cb[key] = cb

        # --- 高级 ---
        fa = tab.tab("高级")
        fa.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(fa, text="监控服务 (monitor)", anchor="w").grid(row=0, column=0, padx=16, pady=(14, 4), sticky='w')
        self.mon_host = ctk.CTkEntry(fa, width=200)
        self.mon_host.grid(row=1, column=0, padx=16, sticky='w')
        self.mon_port = ctk.CTkEntry(fa, width=120)
        self.mon_port.grid(row=1, column=1, padx=16, sticky='w')
        ctk.CTkLabel(fa, text="互斥规则 / 延迟规则（mutex / delay）说明：本次以保留原文件内容为准，"
                               "如需编辑请在 config.ini 中按注释结构手动添加。",
                     text_color="gray60", anchor="w", wraplength=640, justify="left")\
            .grid(row=2, column=0, columnspan=2, padx=16, pady=16, sticky='w')
        ctk.CTkLabel(fa, text="注：保存会重写 config.ini（备份自动存为 config.ini.bak）。",
                     text_color="gray60", anchor="w").grid(row=3, column=0, columnspan=2, padx=16, pady=4, sticky='w')

        # --- 底部按钮（横向滚动，放不下才显示滚动条）---
        btns = ctk.CTkFrame(self)
        btns.grid(row=1, column=0, sticky='ew', padx=12, pady=12)
        btns.grid_columnconfigure(0, weight=1)
        frame_color = self._apply_appearance_mode(btns.cget('fg_color'))
        canvas = tk.Canvas(btns, height=52, highlightthickness=0, bd=0, bg=frame_color)
        xsb = tk.Scrollbar(btns, orient='horizontal', command=canvas.xview)
        canvas.configure(xscrollcommand=xsb.set)
        canvas.grid(row=0, column=0, sticky='ew', padx=(6, 0))
        xsb.grid(row=1, column=0, sticky='ew', padx=(6, 0))
        inner = ctk.CTkFrame(canvas, fg_color="transparent")
        canvas.create_window((0, 0), window=inner, anchor='nw')

        self._btn_labels = [("保存配置", self.save), ("开始选课", self.launch), ("运行状态", self.view_status),
                            ("停止任务", self.stop_task), ("清理日志", self.clear_log),
                            ("日志目录", self.open_log), ("说明", self.open_readme)]
        for i, (txt, cmd) in enumerate(self._btn_labels):
            ctk.CTkButton(inner, text=txt, width=100, command=cmd).grid(row=0, column=i, padx=6, pady=6)
        self.cb_log = ctk.CTkCheckBox(inner, text="记录日志(run.log)", variable=self.log_enabled)
        self.cb_log.grid(row=0, column=len(self._btn_labels), padx=8, pady=6)

        self.status = ctk.CTkLabel(btns, text="就绪", anchor="w")
        self.status.grid(row=2, column=0, sticky='w', padx=14, pady=4)

        def refresh_scroll(event=None):
            inner.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox('all'))
            if inner.winfo_reqwidth() > canvas.winfo_width():
                if not xsb.winfo_ismapped():
                    xsb.grid()
            else:
                if xsb.winfo_ismapped():
                    xsb.grid_remove()
        canvas.bind('<Configure>', refresh_scroll)
        inner.bind('<Configure>', refresh_scroll)

    # ---------- course rows ----------
    def _render_courses(self):
        for w in self._row_widgets.values():
            for wg in w.values():
                wg.destroy()
        self._row_widgets.clear()
        for idx, c in enumerate(self._courses):
            row = ctk.CTkFrame(self.course_frame, fg_color="transparent")
            row.grid(row=idx, column=0, sticky='ew', pady=3)
            e_name = ctk.CTkEntry(row, width=240); e_name.insert(0, c['name'])
            e_class = ctk.CTkEntry(row, width=80); e_class.insert(0, c['klass'])
            e_school = ctk.CTkEntry(row, width=180); e_school.insert(0, c['school'])
            e_name.grid(row=0, column=0, padx=6); e_class.grid(row=0, column=1, padx=6)
            e_school.grid(row=0, column=2, padx=6)
            sel = ctk.CTkRadioButton(row, text="", variable=self.sel_course, value=idx, width=24)
            sel.grid(row=0, column=3, padx=4)
            self._row_widgets[idx] = {'name': e_name, 'class': e_class, 'school': e_school}

    def add_course(self):
        self._courses.append({'id': '', 'name': '', 'klass': '', 'school': ''})
        self._render_courses()

    def remove_course(self):
        idx = self.sel_course.get()
        if 0 <= idx < len(self._courses):
            self._courses.pop(idx)
            if self.sel_course.get() >= len(self._courses):
                self.sel_course.set(max(0, len(self._courses) - 1))
            self._render_courses()

    def move_course(self, delta):
        idx = self.sel_course.get()
        ni = idx + delta
        if 0 <= idx < len(self._courses) and 0 <= ni < len(self._courses):
            self._courses[idx], self._courses[ni] = self._courses[ni], self._courses[idx]
            self.sel_course.set(ni)
            self._render_courses()

    def _fill_ui(self):
        for key in ('student_id', 'password'):
            getattr(self, 'ent_' + key).insert(0, self._get('user', key))
        self.cmb_dual.set("true" if self._get('user', 'dual_degree', 'false').lower() in ('1', 'true', 'yes') else "false")
        self.cmb_ident.set(self._get('user', 'identity', 'bfx'))
        for key, (ent, typ, dflt) in self.param_entries.items():
            v = self._get('client', key, dflt)
            ent.insert(0, v)
            self.param_entries[key] = (ent, typ, dflt)
        for key, cb in self.bool_cb.items():
            cb.select() if self._get('client', key, 'false').lower() in ('1', 'true', 'yes') else cb.deselect()
        self.mon_host.insert(0, self._get('monitor', 'host', '127.0.0.1'))
        self.mon_port.insert(0, self._get('monitor', 'port', '7074'))
        self._render_courses()

    # ---------- actions ----------
    def save(self):
        # 收集当前值
        cp = configparser.ConfigParser(allow_no_value=True)
        cp['user'] = {
            'student_id': self.ent_student_id.get(),
            'password': self.ent_password.get(),
            'dual_degree': 'true' if 'true' in self.cmb_dual.get() else 'false',
            'identity': self.cmb_ident.get(),
        }
        client = {}
        for key, (ent, typ, dflt) in self.param_entries.items():
            raw = ent.get().strip() or str(dflt)
            client[key] = raw
        for key, cb in self.bool_cb.items():
            client[key] = 'true' if cb.get() else 'false'
        cp['client'] = client
        cp['monitor'] = {'host': self.mon_host.get().strip() or '127.0.0.1',
                         'port': self.mon_port.get().strip() or '7074'}
        # 课程：保留原 id 或生成新 id
        used = [c['id'] for c in self._courses if c['id']]
        for i, c in enumerate(self._courses):
            c['name'] = self._row_widgets[i]['name'].get().strip()
            c['klass'] = self._row_widgets[i]['class'].get().strip()
            c['school'] = self._row_widgets[i]['school'].get().strip()
            cid = c['id']
            if not cid or cid in used:
                j = 0
                while ('course_%d' % j) in used:
                    j += 1
                cid = 'course_%d' % j
                used.append(cid)
            cp['course:%s' % cid] = {'name': c['name'], 'class': c['klass'], 'school': c['school']}
        # 保留原 mutex / delay（透传）
        for sec in self.cfg.sections():
            if sec.startswith(('mutex:', 'delay:')):
                cp[sec] = dict(self.cfg.items(sec))
        # 备份 + 写
        try:
            if os.path.exists(CONFIG):
                import shutil; shutil.copy2(CONFIG, CONFIG + '.bak')
            with open(CONFIG, 'w', encoding='utf-8') as fp:
                cp.write(fp)
            self.status.configure(text="已保存（备份: config.ini.bak）")
        except Exception as e:
            self.status.configure(text="保存失败：%s" % e)

    def launch(self):
        self.save()
        if self.proc is not None and self.proc.poll() is None:
            self.status.configure(text="任务已在后台运行。")
            return
        self.status.configure(text="后台运行中 ...")
        os.makedirs(os.path.join(BASE, 'log'), exist_ok=True)

        def run():
            try:
                flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)  # 不弹出控制台窗口
                use_log = self.log_enabled.get()
                if use_log:
                    self.proc = subprocess.Popen([sys.executable, os.path.join(BASE, 'main.py')],
                                                 cwd=BASE, stdout=subprocess.PIPE,
                                                 stderr=subprocess.STDOUT, creationflags=flags)
                    # 读取输出写入日志，防止管道阻塞
                    with open(os.path.join(BASE, 'log', 'run.log'), 'wb') as logf:
                        for line in iter(self.proc.stdout.readline, b''):
                            logf.write(line)
                            logf.flush()
                else:
                    # 不记录日志：丢弃输出
                    self.proc = subprocess.Popen([sys.executable, os.path.join(BASE, 'main.py')],
                                                 cwd=BASE, stdout=subprocess.DEVNULL,
                                                 stderr=subprocess.DEVNULL, creationflags=flags)
                rc = self.proc.wait()
                self.after(0, lambda rc=rc: self.notify_done(rc))
            except Exception as e:
                self.after(0, lambda: self.status.configure(text="启动失败：%s" % e))
        threading.Thread(target=run, daemon=True).start()

    def stop_task(self):
        p = self.proc
        if p is not None and p.poll() is None:
            try:
                p.terminate()
            except Exception:
                pass
            self.status.configure(text="已请求停止任务。")
        else:
            self.status.configure(text="当前没有运行中的任务。")

    def notify_done(self, rc):
        self.status.configure(text="任务结束（退出码 %s）" % rc)
        try:
            messagebox.showinfo("选课任务", "任务已结束（退出码 %s）。" % rc)
        except Exception:
            pass

    def on_close(self):
        self.stop_task()
        self.destroy()

    def view_status(self):
        """打开实时运行状态/日志窗口（后台任务无控制台，用这个看进度）。"""
        win = ctk.CTkToplevel(self)
        win.title("运行状态 / 日志")
        win.geometry("720x470")
        win.grid_columnconfigure(0, weight=1)
        win.grid_rowconfigure(0, weight=1)

        box = ctk.CTkTextbox(win, wrap='none', font=("Consolas", 11))
        box.grid(row=0, column=0, sticky='nsew', padx=8, pady=8)

        bar = ctk.CTkFrame(win)
        bar.grid(row=1, column=0, sticky='ew', padx=8, pady=6)
        status = ctk.CTkLabel(bar, text="", anchor="w")
        status.grid(row=0, column=0, sticky='w', padx=8)
        ctk.CTkButton(bar, text="停止任务", width=100, command=self.stop_task)\
            .grid(row=0, column=1, padx=8)

        def refresh():
            if not win.winfo_exists():
                return
            p = os.path.join(BASE, 'log', 'run.log')
            try:
                data = open(p, encoding='utf-8', errors='replace').read() if os.path.exists(p) else "(暂无日志)"
            except Exception as e:
                data = "读取日志失败：%s" % e
            box.delete('1.0', 'end')
            box.insert('1.0', data)
            box.see('end')
            running = self.proc is not None and self.proc.poll() is None
            status.configure(text="状态：" + ("后台运行中" if running else "已停止 / 任务结束"))
            win.after(1500, refresh)

        refresh()

    def clear_log(self):
        if not messagebox.askyesno("清理日志", "确定清空 log 目录下的日志文件吗？"):
            return
        logdir = os.path.join(BASE, 'log')
        removed = 0
        if os.path.isdir(logdir):
            for fn in os.listdir(logdir):
                fp = os.path.join(logdir, fn)
                if os.path.isfile(fp):
                    try:
                        os.remove(fp)
                        removed += 1
                    except Exception:
                        pass
        self.status.configure(text="已清理 %d 个日志文件" % removed)

    def open_log(self):
        logdir = os.path.join(BASE, 'log')
        if os.path.isdir(logdir):
            os.startfile(logdir)
        else:
            self.status.configure(text="未找到 log 目录")

    def open_readme(self):
        p = os.path.join(BASE, 'README.md')
        if os.path.exists(p):
            os.startfile(p)


if __name__ == '__main__':
    App().mainloop()
