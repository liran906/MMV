#!/usr/bin/env python
# _*_ coding:utf-8 _*_
#
# @Version : 2.2
# @Time    : 2024/2/17 10:14
# @Author  : lir906
# @File    : main2.2.py

from tkinter import *
from datetime import datetime, timedelta
from collections import OrderedDict
from random import shuffle
import tkinter.messagebox as mbox
import json, os, shutil, re, threading, time, queue

from Words import WordDefinition
import Sound

def version_discriptions():
    print(
        '版本信息\n'
        'v1.0 2024.2.13\n初始版本,提供输入词汇窗口,并根据输入词汇生成词库,可以根据需要选择复习今日词汇或复习遗忘词汇\n'+
        'v2.0 2024.2.16\nUI界面重新设计\n增加词汇释义功能\n'+
        'v2.1 2024.2.17\n增加复习所有词汇功能\n复习时对其余复习选项锁定,反之亦然\n'+
        'v2.2 2024.2.20\n增加中文翻译结果，并可手动修改（有道的翻译有时候是真不准啊）\n增加单词语音播放\n增加按录入顺序复习选项\n增加单词默写检查功能\n增加提前结束当前复习功能\n增加复习时间及时长显示\n增加输入框默认提示\n'
        'v2.3 2024.2.24\n增加听音拼写和看义拼写两种拼写模式\n增加当前剩余单词数量、错误单词数量、总体单词数量统计\n修复了默写功能的逻辑bug\n后面应该暂时不再更新，要专心背单词了\n现在每多加一个功能都很困难，要调整前面各种方法中的代码，还可能产生意想不到的逻辑错误，体会到了代码可维护性的重要'
    )

class VocabApp(Frame):
    def __init__(self):
        # 窗口基本初始化设置
        Frame.__init__(self)
        self.master.geometry('1280x540')
        self.master.title('MMV - Memorize My Vocabs v2.3')
        self.master.protocol('WM_DELETE_WINDOW', self.exit)
        self.master.option_add('*Font', 'Helvetica 14')
        self.pack()

        # 文件路径初始化
        self.save_dir = r'.\vocabulary\save'
        self.dir_init(self.save_dir)
        self.review_dir = r'.\vocabulary\save\review'
        self.dir_init(self.review_dir)

        # 时间初始化
        self.cur_dt = datetime.now().date()
        self.str_dt = self.cur_dt.strftime('%Y%m%d')
        self.time_init = time.time()
        # timer_thread = threading.Thread(target=self.timer, daemon=True)
        self.time_queue1 = queue.Queue()
        self.time_queue2 = queue.Queue()
        self.time_queue3 = queue.Queue()
        self.time_display_p1 = self.time_init
        self.time_display_p2 = self.time_init
        self.time_display_p3 = 0
        self.counter_status = '余/误/总：0/0/0'

        # 变量初始化
        self.review_date = ['1','2','4','7']
        self.rv_list = []
        self.rv_dict = {}
        self.rv_count = 0

        self.td_in_list = []
        self.td_out_list = []

        self.al_in_list = []
        self.al_out_list = []

        self.new_w = None
        self.previous_w = None
        self.previous_wl = []

        # 状态开关
        self.td_flag = False
        self.rv_flag = False
        self.al_flag = False
        self.rv_saved = False
        self.rv_flag_4time = False
        self.al_null = False
        self.previous_flag = False
        self.recite_flag = False
        self.order_flag = True
        
        # 函数
        self.createWidgets()
        # timer_thread.start()
        version_discriptions()
        self.rv_check()
        self.timer()

    def createWidgets(self): # GUI子控件
        # 输入栏
        self.Entry_1 = Entry(self, text='dcc')
        self.Entry_1.config(font=("Helvetica",18), fg='grey', justify=CENTER)
        self.Entry_1.insert(0, "请在此处输入词汇")
        self.Entry_1.bind('<Button-1>', self.on_entry_click)
        self.Entry_1.grid(row=0, column=0, padx=12, pady=8, columnspan=2, sticky=NSEW)

        # 中间显示区域
        self.txt_display = StringVar()
        self.txt_display.set('Hello!')
        self.time_display = StringVar()

        self.time_area = Label(self, textvariable=self.time_display, font=("等线",12))
        self.time_area.grid(row=0, column=2, columnspan=2, sticky=NS)

        self.word_area = Label(self, textvariable=self.txt_display, font=("Helvetica",32,'bold'))
        self.word_area.grid(row=1, column=2, columnspan=2, sticky=NSEW)
        self.word_area.config(width=20)
        self.word_area.bind('<Button-1>', self.playsound)
        

        self.defn_area = Text(self, font=("Times", 12), wrap='word', height=1, bg= "#F5F5F5", state=DISABLED)
        self.defn_area.grid(row=2, column=2, columnspan=1, rowspan=5, pady=(3, 6), sticky=NSEW)
        self.scrollbar_m2 = Scrollbar(self,width=5)
        self.scrollbar_m2.grid()

        # 日志框
        self.log_box = Text(self, font=("Times", 12), wrap='word', height=6, state=DISABLED, bg= "#F5F5F5")
        self.log_box.grid(row=0, column=4, padx=12, pady=8, rowspan=2, columnspan=2, sticky=NSEW)
        self.log_box.config(width=30)

        # 左侧菜单按钮
        self.button_order = Button(self, text='顺序复习', font=("等线", 14), command=self.order_btn)
        self.button_order.grid(row=1, column=1, padx=(3,12), pady=3, sticky=EW)
        self.button_order.config(width=15)
        self.button_submit = Button(self, text='提交新词汇', font=("等线", 14), command=self.vocab_submit)
        self.button_submit.grid(row=1, padx=(12,3), pady=3, sticky=EW)
        self.button_submit.config(width=15)
        self.button_today = Button(self, text='今日词汇', font=("等线", 14), command=self.td_walk)
        self.button_today.grid(row=2, padx=(12,3), pady=3, sticky=EW)
        self.button_review = Button(self, text='以往词汇', font=("等线", 14), command=self.rv_walk)
        self.button_review.grid(row=3, padx=(12,3), pady=3, sticky=EW)
        self.button_all = Button(self, text='所有词汇', font=("等线", 14), command=self.al_walk)
        self.button_all.grid(row=4, padx=(12,3), pady=3, sticky=EW)
        self.button_amend = Button(self, text='更改注释', font=("等线", 14), state=DISABLED, command=self.amend_1)
        self.button_amend.grid(row=2, column=1, padx=(3,12), pady=3, sticky=EW)


        # 错题本相关功能按钮
        self.button_sradd = Button(self, text='加入错题本', font=("等线", 14), state=DISABLED)
        self.button_sradd.grid(row=3, column=1, padx=(3,12), pady=3, sticky=EW)
        self.button_srpop = Button(self, text='移出错题本', font=("等线", 14), state=DISABLED)
        self.button_srpop.grid(row=4, column=1, padx=(3,12), pady=3, sticky=EW)

        # 默写
        self.button_recite = Button(self, text='拼写检查', font=("等线", 14), state=DISABLED, command=self.recite)
        self.button_recite.grid(row=5, column=1, padx=(3,12), pady=3, sticky=EW)
        self.button_recitemode = Button(self, text='听音拼写', font=("等线", 14), state=DISABLED, command=self.recite_change_mode)
        self.button_recitemode.grid(row=5, padx=(12,3), pady=(3, 6), sticky=EW)
        
        # 功能按钮：列1
        self.button_yes = Button(self, text='记住了', font=("等线", 14), state=DISABLED, command=self.yes_btn)
        self.button_yes.grid(row=2, column=4, padx=(12,3), pady=3, sticky=EW)
        self.button_hint = Button(self, text='提示', font=("等线", 14), state=DISABLED, command=self.hint_btn)
        self.button_hint.grid(row=3, column=4, padx=(12,3), pady=3, sticky=EW)
        self.button_no = Button(self, text='没记住', font=("等线", 14), state=DISABLED, command=self.no_btn)
        self.button_no.grid(row=4, column=4, padx=(12,3), pady=3, sticky=EW)
        self.button_exit = Button(self, text='保存并退出', font=("等线", 14), command=self.exit)
        self.button_exit.grid(row=5, column=4, padx=12, pady=(3, 6), columnspan=2, sticky=EW)
        self.button_yes.config(width=11) # 列宽
        # 功能按钮：列2
        self.button_previous = Button(self, text='上个单词', font=("等线", 14), state=DISABLED, command=self.show_previous_w)
        self.button_previous.grid(row=2, column=5, padx=(3,12), pady=3, sticky=EW)
        self.button_back = Button(self, text='回到当前', font=("等线", 14), state=DISABLED, command=self.back_2current)
        self.button_back.grid(row=3, column=5, padx=(3,12), pady=3, sticky=EW)
        self.button_reset = Button(self, text='结束本轮', font=("等线", 14), state=DISABLED, command=self.early_quit)
        self.button_reset.grid(row=4, column=5, padx=(3,12), pady=3, sticky=EW)
        self.button_previous.config(width=11) # 列宽

        self.menu_button_set = {
            self.button_submit, self.button_today, self.button_review, self.button_all, self.button_order
        }
        self.function_button_set = {
            self.button_previous, self.button_reset, self.button_recite,
            self.button_yes, self.button_hint, self.button_no
        }

        for b in {
            self.button_order, self.button_submit, self.button_today, self.button_review, self.button_all,
            self.button_previous, self.button_back, self.button_reset, self.button_recite,
            self.button_yes, self.button_hint, self.button_no, self.button_recitemode,self.button_exit,
            self.button_sradd, self.button_amend, self.button_srpop
        }:
            b.config(height=4) # 统一设置行高
        
        # 快捷键
        self.Entry_1.bind('<Return>', lambda event: self.vocab_submit())
        self.defn_area.bind('<Return>', lambda event: self.amend_2())
        self.master.bind('<Escape>', lambda event: self.exit_messagebox())
        self.master.bind('<KeyPress-F1>', lambda event: self.playsound(event))
        self.master.bind('<KeyPress-F2>', lambda event: self.button_hint.invoke())

    # BUTTON FUNCTION PACK
    def yes_btn(self):
        if self.td_flag:
            self.td_remove_list.add(self.new_w)
        elif self.rv_flag:
            self.rv_remove_list.add(self.new_w)
        elif self.al_flag:
            self.al_remove_list.add(self.new_w)
        self.defn_area.config(state=NORMAL)
        self.defn_area.delete('1.0','end')
        self.defn_area.config(state=DISABLED)
        self.gen_next_word()
        self.count_yes()
        if self.recite_flag:
            self.button_yes.config(state=DISABLED)
        if self.button_amend.cget('state') == 'normal':
            self.button_amend.config(state=DISABLED)

    def no_btn(self):
        self.defn_area.config(state=NORMAL)
        self.defn_area.delete('1.0','end')
        if self.recite_flag and self.button_no.cget('text') == '没记住':
            self.txt_display.set(self.new_w)
            self.defn_area.insert('1.0',self.def_after_judge)
            self.defn_area.config(state=DISABLED)
            Sound.play_mp3(self.new_w)
            self.button_yes.config(state=DISABLED)
            self.button_no.config(text='下一个')
            return
        self.defn_area.config(state=DISABLED)
        self.gen_next_word()
        self.count_no()
        if self.recite_flag:
            self.button_no.config(text='没记住')
            self.button_yes.config(state=DISABLED)
        if self.button_amend.cget('state') == 'normal':
            self.button_amend.config(state=DISABLED)

    def hint_btn(self):
        self.defn_area.config(state=NORMAL)
        self.defn_area.delete('1.0','end')
        self.defn_area.insert('1.0', self.get_definition())
        self.defn_area.config(state=DISABLED)
        self.button_amend.config(state=NORMAL)

    def order_btn(self):
        if self.button_order.cget('text') == '顺序复习':
            self.button_order.config(text = '乱序复习')
        elif self.button_order.cget('text') == '乱序复习':
            self.button_order.config(text = '顺序复习')

    def btn_switch(self):
        def switch_status(btn):
            if btn.cget('state') == 'normal':
                btn.config(state = DISABLED)
            elif btn.cget('state') == 'disabled':
                btn.config(state = NORMAL)

        self.defn_area.config(state=NORMAL)
        self.defn_area.delete('1.0','end')
        self.defn_area.config(state=DISABLED)
        for btn in self.menu_button_set:
            switch_status(btn)
        for btn in self.function_button_set:
            switch_status(btn)

    def on_entry_click(self, event):
        if self.Entry_1.get() == "请在此处输入词汇":
            self.Entry_1.delete(0,END)
            self.Entry_1.config(fg='black')
    
    def early_quit(self):
        if self.td_flag:
            self.td_announce()
        elif self.rv_flag:
            self.rv_announce()
        elif self.al_flag:
            self.al_announce()

    # GENERAL FUNCTION PACK: GENERAL
    def get_definition(self):
        if hasattr(self, 'thread_loop') and self.thread_loop and threading.current_thread().name == 'MainThread': # 在这里回收子进程 也不知道成功没有
            self.thread_loop.join()
        if self.new_w:
            definition = WordDefinition(self.new_w)
        elif self.vocab_in:
            try:
                definition = WordDefinition(self.vocab_in)
                self.td_in_list.append(self.vocab_in.lower())
                self.txt_display.set(self.vocab_in)
                self.defn_area.config(state=NORMAL)
                self.defn_area.delete('1.0','end')
                self.defn_area.insert('1.0', definition.publish)
                self.defn_area.config(state=DISABLED)
                self.button_amend.config(state=NORMAL)
                Sound.check_exist(self.vocab_in)
            except TypeError as e:
                print(datetime.now().strftime('%H:%M:%S')+':',e)
                mbox.showerror('单词有误','单词%s有误，请检查拼写，然后重试' % self.vocab_in)
                return
        if self.recite_flag:
            self.def_after_judge = definition.publish
            return definition.chinese_only
        return definition.publish

    def dir_init(self,pathordir): # 路径或文件初始化
        if not os.path.exists(pathordir):
            if '.' in pathordir[1:]:
                with open(pathordir,'w'):
                    pass
            else:
                os.makedirs(pathordir)

    def save(self, prefix = 'TD', rf_strdt = None): # 保存
        if prefix == 'TD':
            if self.td_in_list == []:
                return
            file_path = os.path.join(self.save_dir, prefix+self.str_dt+'.txt')
            self.dir_init(file_path)
            with open(file_path,'r') as f:
                existing_words = {line.strip() for line in f.readlines()}
            self.td_in_list = list(OrderedDict.fromkeys(self.td_in_list)) # 本身去重
            new_words = [i for i in self.td_in_list if i not in existing_words] # 与现有存档再次去重
            with open(file_path,'a') as f:
                for i in new_words:
                    f.write(i+'\n')
            self.init_review_file() # 存储成功则生成今日的reviewfile

        elif prefix == 'RV':
            if self.rv_list == []:
                return
            file_path = os.path.join(self.save_dir, prefix+self.str_dt+'.txt')
            self.dir_init(file_path)
            with open(file_path,'w') as f:
                for i in self.rv_list:
                    f.write(i+'\n')

        elif prefix == 'RF':
            if rf_strdt == None:
                rf_strdt = self.str_dt
            file_path = os.path.join(self.review_dir, prefix+rf_strdt+'.txt')
            self.dir_init(self.review_dir)
            self.dir_init(file_path)
            with open(file_path,'w') as f:
                f.write(json.dumps(self.rv_dict))
        
        elif prefix == 'AL':
            if self.al_in_list == []:
                return
            file_path = os.path.join(self.save_dir, prefix+self.str_dt+'.txt')
            if self.al_maxdt == 0:
                self.dir_init(file_path)
            else:
                shutil.copy(self.save_dir+r'\AL'+self.al_maxdt+'.txt', file_path)
            with open(file_path,'a') as f:
                for i in self.al_in_list:
                    f.write(i+'\n')
    
    def load(self, prefix = 'TD', *rvdt): # 读取
        if prefix == 'TD':
            file_path = os.path.join(self.save_dir, prefix+self.str_dt+'.txt')
            if not os.path.exists(file_path):
                return
            with open(file_path,'r') as f:
                return [line.strip() for line in f.readlines()]
            
        elif prefix == 'RV':
            file_path = os.path.join(self.save_dir, prefix+self.str_dt+'.txt')
            if not os.path.exists(file_path):
                return
            with open(file_path,'r') as f:
                return [line.strip() for line in f.readlines()]
            
        elif prefix == 'RF':
            file_path = os.path.join(self.review_dir, prefix+rvdt[0]+'.txt')
            if not os.path.exists(file_path):
                return
            with open(file_path,'r') as f:
                return json.loads(f.readline())
        
        elif prefix == 'AL':
            file_path = os.path.join(self.save_dir, prefix+self.str_dt+'.txt')
            if not os.path.exists(file_path):
                return
            with open(file_path,'r') as f:
                return [line.strip() for line in f.readlines()]

    def exit(self):
        self.save()
        self.quit()
    
    def exit_messagebox(self):
        result = mbox.askquestion('保存并退出','是否要保存并退出？')
        if result == 'yes':
            self.exit()
        else:
            pass

    # GENERAL FUNCTION PACK: TIMING & COUNTING
    def timer(self):
        # if self.time_init >= time.time()-2:
        #     self.timing3 = ''
        try:
            self.time_queue1.put(str(time.strftime("%d %h %X")))
            self.time_queue2.put(str(timedelta(seconds=int(time.time() - self.time_init))))
            # if any([self.td_out_list, self.al_out_list, self.rv_flag_4time]):
            #     self.time_queue3.put(str(timedelta(seconds=int(time.time() - self.time_td))))
            #     last_record = str(timedelta(seconds=int(time.time() - self.time_td)))
            #     self.timing3 = '本轮复习时长：'+self.time_queue3.get_nowait()
            # else:
            #     if not self.timing3:
            #         self.timing3 = '上轮复习时长：00:00:00'
            #     elif self.timing3 == '上轮复习时长：00:00:00':
            #         pass
            #     else:
            #         if last_record in locals():
            #             self.timing3 = '上轮复习时长：'+last_record
            self.timing1 = '当前时间：'+self.time_queue1.get_nowait()
            self.timing2 = '本次时长:'+self.time_queue2.get_nowait()
            self.time_display.set(self.timing1+'        '+self.timing2+'        '+self.counter_status) # 更新GUI
        except queue.Empty:
            pass
        finally:
            self.master.after(1000, self.timer) # recurision

    def counter(self):
        self.num_undone -= 1
        self.counter_status = '余/误/总：%d/%d/%d' % (self.num_undone, self.num_undone+self.counter_no, self.num_all)
        self.time_display.set(self.timing1+'        '+self.timing2+'        '+self.counter_status)
        pass

    def count_yes(self):
        self.counter_yes += 1
        self.counter()
        pass

    def count_no(self):
        self.counter_no += 1
        self.counter()

    def counter_init(self):
        if self.td_flag:
            self.num_all = self.td_num_all
            self.num_undone = self.td_num_undone
        elif self.rv_flag:
            self.num_all = self.rv_num_all
            self.num_undone = self.rv_num_undone
        elif self.al_flag:
            self.num_all = self.al_num_all
            self.num_undone = self.al_num_undone
        self.counter_yes = 0
        self.counter_no = 0
        self.counter_status = '余/误/总：%d/%d/%d' % (self.num_undone, self.num_undone+self.counter_no, self.num_all)
        self.time_display.set(self.timing1+'        '+self.timing2+'        '+self.counter_status)

    # GENERAL FUNCTION PACK: WORD DISPLAY
    def init_generator(self, lst): # 翻牌
        tmp = list(lst)
        if not self.previous_flag:
            if self.button_order.cget('text') == '乱序复习':
                shuffle(tmp)
        for i in tmp:
            yield i

    def gen_next_word(self):
        try:
            if self.previous_flag:
                self.new_w = next(self.pre_generator)
            else:
                if self.new_w:
                    self.previous_wl.append(self.new_w)
                if self.td_flag:
                    self.new_w = next(self.td_generator)
                elif self.rv_flag:
                    self.new_w = next(self.rv_generator)
                elif self.al_flag:
                    self.new_w = next(self.al_generator)
            if self.recite_flag:
                self.txt_display.set('input in entry box')
                self.recite_afoot()
            else:
                self.txt_display.set(self.new_w)
        except StopIteration:
            self.new_w = None
            if self.previous_flag:
                mbox.showinfo('上个单词','已经到达第一个单词了')
                self.back_2current()
            else:
                if self.recite_flag:
                    self.recite()
                if self.td_flag:
                    self.td_announce()
                elif self.rv_flag:
                    self.rv_announce()
                elif self.al_flag:
                    self.al_announce()
    
    def show_previous_w(self):
        if not self.previous_flag:
            self.previous_flag = True
            self.current_w = self.new_w
            self.pre_generator = self.init_generator(self.previous_wl[::-1])
            self.button_recite.config(state=DISABLED)
            self.button_yes.config(state=DISABLED)
            self.button_no.config(state=DISABLED)
            self.button_back.config(state=NORMAL)
        self.gen_next_word()
        self.defn_area.config(state=NORMAL)
        self.defn_area.delete('1.0','end')
        self.defn_area.config(state=DISABLED)
        if self.button_amend.cget('state') == 'normal':
            self.button_amend.config(state=DISABLED)
    
    def back_2current(self):
        self.previous_flag = False
        self.new_w = self.current_w
        self.txt_display.set(self.new_w)
        self.button_recite.config(state=NORMAL)
        self.button_yes.config(state=NORMAL)
        self.button_no.config(state=NORMAL)
        self.defn_area.config(state=NORMAL)
        self.defn_area.delete('1.0','end')
        self.defn_area.config(state=DISABLED)
        self.button_back.config(state=DISABLED)

    def reset_list(self):
        if self.td_flag:
            pass

    def amend_1(self):
        self.defn_area.config(state=NORMAL, bg= "white")
        self.button_amend.config(text='提交注释', command=self.amend_2)
        self.prev_cn = self.defn_area.get("1.3", "1.end")
        for b in self.function_button_set:
            b.config(state=DISABLED)
        for b in self.menu_button_set:
            b.config(state=DISABLED)
        self.button_back.config(state=DISABLED)
    
    def amend_2(self):
        amend_input = self.defn_area.get("1.3", "1.end")
        self.defn_area.config(state=DISABLED, bg= "#F5F5F5")
        self.button_amend.config(text='更改注释', command=self.amend_1)
        if self.new_w:
            for b in self.function_button_set:
               b.config(state=NORMAL)
            amend_content = self.new_w
        elif self.vocab_in:
            for b in self.menu_button_set:
               b.config(state=NORMAL)
            amend_content = self.vocab_in
        if self.previous_flag:
            self.button_back.config(state=NORMAL)
            self.button_yes.config(state=DISABLED)
            self.button_no.config(state=DISABLED)
        if amend_input != self.prev_cn: # 有修改
            amend_w = WordDefinition(amend_content)
            amend_w.alter_cn_result(amend_input)

    def percentage(self, denominator): # undone
        pass


    # GENERAL FUNCTION PACK: VOCAL
    def playsound(self, event):
        if self.new_w:
            Sound.play_mp3(self.new_w)
        elif self.vocab_in:
            Sound.play_mp3(self.vocab_in)

    # TD FUNCTION PACK
    def vocab_submit(self): # 输入单词
        if any([self.td_flag, self.rv_flag, self.al_flag]) and not self.recite_flag:
            self.Entry_1.delete(0, END)
            return
        self.vocab_in = self.Entry_1.get().lower()
        if self.recite_flag and not self.recite_count and self.vocab_in == '' and not self.word_area.cget('text') == 'Input in Entry box':
            self.yes_btn()
            return
        if self.recite_flag and self.recite_count >= 1 and self.vocab_in == '':
            self.no_btn()
            return
        if re.match("^[a-zA-Z]+$", self.vocab_in) is None:
            mbox.showinfo('Message', '请正确输入单个词汇')
            self.Entry_1.delete(0, END)
            return
        if self.vocab_in == '' or None:
            return
        self.Entry_1.delete(0, END)
        if self.recite_flag: # 默写模式
            self.get_definition()
            self.recite_judge()
            return
        self.thread_loop = threading.Thread(target=self.get_definition) # 后台加载
        self.thread_loop.start()
        # self.thread_vocal = threading.Thread(target=Sound.check_exist, args=self.vocab_in)
        # self.thread_vocal.start()
    
    def td_walk(self): # 今日单词复习
        self.save()
        if len(self.td_out_list) == 0:
            self.td_out_list = self.load()
            self.td_num_all = len(self.td_out_list)
            self.time_td = time.time()
            if not self.td_out_list: # 没有今日单词,save方法确定了保存文件不会是空白的
                mbox.showinfo('今日词汇复习','今日没有可复习词汇')
                self.td_out_list = [] # 重新初始化outlist
                return
        self.td_num_undone = len(self.td_out_list)
        self.btn_switch()
        mbox.showinfo('今日词汇复习','本轮复习共计%d个单词，马上开始' % self.td_num_undone)
        self.td_generator = self.init_generator(self.td_out_list)
        self.td_remove_list = set()
        self.td_flag = True
        self.gen_next_word()
        self.counter_init()

    def td_announce(self):
        self.txt_display.set('Hello!')
        self.td_out_list = [i for i in self.td_out_list if i not in self.td_remove_list]
        self.td_flag = False
        self.btn_switch()
        mbox.showinfo(
            '今日词汇复习','本轮完成！已掌握%d个词汇,未掌握%d个词汇'
            % (len(self.td_remove_list),len(self.td_out_list))
            )
        if len(self.td_out_list) == 0:
            mbox.showinfo('今日词汇复习','今日词汇列表重置')

    # RV FUNCTION PACK
    def init_review_file(self): # 初始化今天的复习文件 已绑定到self.save
        if not self.rv_saved:
            rvdt_4dict = [False]*len(self.review_date)
            self.rv_dict = dict(zip(self.review_date, rvdt_4dict))
            self.save('RF')
            self.rv_saved = True
    
    def rv_check(self, check_dt = None): # 检查今天的复习任务
        if check_dt == None:
            check_dt = self.cur_dt
        rv_strdt = [(check_dt-timedelta(days=int(d))).strftime('%Y%m%d') for d in self.review_date]
        rv_start_flag = False
        for index, strdt in enumerate(rv_strdt):
            rv_dict = self.load('RF', strdt)
            if not rv_dict:
                continue
            if not rv_dict[self.review_date[index]]:
                self.rv_enroll(strdt)
                rv_start_flag = True
            # elif: # 更早是否复习的检测
            pass # 要把dict中的值改为true
        if rv_start_flag:
            self.save('RV')
            self.rv_num_all = len(self.rv_list)
            mbox.showinfo('注意','今天有需要复习的词汇共计%d个' % self.rv_num_all)
    
    def rv_enroll(self,strdate): # 把对应日期的词汇表导入复习列表中
        file_path = os.path.join(self.save_dir, 'TD'+strdate+'.txt')
        with open(file_path,'r') as f:
            rv_enroll_list = [word.strip() for word in f.readlines()]
        self.rv_list = list(OrderedDict.fromkeys(self.rv_list + rv_enroll_list))
    
    def rv_walk(self):
        if len(self.rv_list) == 0:
            self.rv_list = self.load('RV')
            self.rv_num_all = len(self.rv_list)
            self.time_td = time.time()
            if not self.rv_list: # 没有今日单词,save方法确定了保存文件不会是空白的
                mbox.showinfo('以往词汇复习','今日没有可复习词汇')
                self.rv_list = [] # 重新初始化outlist
                return
        self.rv_count += 1
        if self.rv_count == 1:
            self.time_td = time.time()
        self.rv_num_undone = len(self.rv_list)
        self.btn_switch()
        mbox.showinfo('以往词汇复习','本轮复习共计%d个单词，马上开始' % self.rv_num_undone)
        self.rv_generator = self.init_generator(self.rv_list)
        self.rv_remove_list = set()
        self.rv_flag = True
        self.rv_flag_4time = True
        self.gen_next_word()
        self.counter_init()
    
    def rv_announce(self):
        self.txt_display.set('Hello!')
        self.rv_list = [i for i in self.rv_list if i not in self.rv_remove_list]
        self.rv_flag = False
        self.btn_switch()
        mbox.showinfo(
            '以往词汇复习','本轮完成！已掌握%d个词汇,未掌握%d个词汇'
            % (len(self.rv_remove_list),len(self.rv_list))
            )
        if len(self.rv_list) == 0:
            self.rv_flag_4time = False
            self.rvfile_adjust()
            mbox.showinfo('以往词汇复习','以往词汇列表已重置')
    
    def rvfile_adjust(self, check_dt = None): # 如果全部掌握一遍，修改对应rf值为true
        if check_dt == None:
            check_dt = self.cur_dt
        rv_strdt = [(check_dt-timedelta(days=int(d))).strftime('%Y%m%d') for d in self.review_date]
        for index, strdt in enumerate(rv_strdt):
            rv_dict = self.load('RF', strdt)
            if not rv_dict:
                continue
            rv_dict[self.review_date[index]] = True
            self.rv_dict = rv_dict
            self.save('RF', strdt)

    #AL FUNCTION PACK
    def al_enroll(self):
        pth = os.path.join(self.save_dir, 'AL' + self.str_dt + '.txt')
        if os.path.exists(pth): # 有今天的AL文件
            return
        filelist = [f.strip('.txt') for f in os.listdir(self.save_dir) if '.txt' in f]
        td_filelist = []
        al_filelist = []
        for f in filelist:
            if 'TD' in f:
                td_filelist.append(f.strip('TD'))
            elif 'AL' in f:
                al_filelist.append(f.strip('AL'))
        if len(td_filelist) == 0:
            self.al_null = True
            return
        
        
        self.al_maxdt = 0
        if len(al_filelist) > 0:
            self.al_maxdt = max(al_filelist)
        td_filelist = sorted(td_filelist, reverse=True)
        enroll_strdt_list = []
        for td_dt in td_filelist: # 判断比al最新日期大的td日期
            if int(td_dt) < int(self.al_maxdt):
                break
            enroll_strdt_list.append(td_dt)
        try:
            enroll_strdt_list.remove(self.str_dt) # 去掉今日（如有）
        except ValueError:
            pass
        for s in enroll_strdt_list: # 从该日期开始导入单词
            file_path = os.path.join(self.save_dir, 'TD'+s+'.txt')
            with open(file_path, 'r') as f:
                for line in f.readlines():
                    self.al_in_list.append(line.strip()) # 不含今日的单词列表
        self.save('AL') # 这里undone

    def al_walk(self):
        self.al_enroll()
        if self.al_null: # 没有td文件可供读取
            mbox.showinfo('所有复习词汇','目前没有可复习的词汇')
            self.al_null = False
            return
        if len(self.al_out_list) == 0:
            self.save()
            if os.path.exists(os.path.join(self.save_dir, 'TD'+self.str_dt+'.txt')): # td不为空
                self.al_out_list = self.load('AL') + self.load()
            else: # td为空
                self.al_out_list = self.load('AL')
            self.time_td = time.time()
            self.al_num_all = len(self.al_out_list)
            if not self.al_out_list: # 只有今日单词
                    mbox.showinfo('所有词汇复习','目前词库中只有今日单词，请直接使用“今日词汇复习”功能')
                    self.al_out_list = [] # 重新初始化outlist
                    return
        self.al_num_undone = len(self.al_out_list)
        self.btn_switch()
        mbox.showinfo('所有词汇复习','本轮复习共计%d个单词，马上开始' % self.al_num_undone)
        self.al_generator = self.init_generator(self.al_out_list)
        self.al_remove_list = set()
        self.al_flag = True
        self.gen_next_word()
        self.counter_init()

    def al_announce(self):
        self.txt_display.set('Hello!')
        self.al_out_list = [i for i in self.al_out_list if i not in self.al_remove_list]
        self.al_flag = False
        self.btn_switch()
        mbox.showinfo(
            '所有词汇复习','本轮完成！已掌握%d个词汇,未掌握%d个词汇'
            % (len(self.al_remove_list),len(self.al_out_list))
            )
        if len(self.al_out_list) == 0:
            mbox.showinfo('所有词汇复习','所有词汇列表已重置')
    
    # RECITE FUNCTION PACK
    def recite(self):
        if not self.recite_flag:
            self.recite_flag = True
            self.button_recitemode.config(state=NORMAL)
            self.button_recite.config(text='拼写中')
            self.button_yes.config(text='下一个')
            self.defn_area.config(state=NORMAL)
            self.defn_area.delete('1.0','end')
            if self.button_recitemode.cget('text') == '看义拼写':
                self.defn_area.insert('1.0', self.get_definition())
            self.defn_area.config(state=DISABLED)
            self.button_yes.config(state=DISABLED)
            self.button_hint.config(state=DISABLED)
            self.button_previous.config(state=DISABLED)
            self.txt_display.set('Input in Entry box')
            self.recite_count = 0
            if self.button_recitemode.cget('text') == '听音拼写':
                Sound.play_mp3(self.new_w)
        else:
            self.recite_flag = False
            self.button_recitemode.config(state=DISABLED)
            self.button_yes.config(state=NORMAL)
            self.button_hint.config(state=NORMAL)
            self.button_previous.config(state=NORMAL)
            self.button_recite.config(text='拼写检查')
            self.button_yes.config(text='记住了')
            self.button_no.config(text='没记住')
            self.defn_area.config(state=NORMAL)
            self.defn_area.delete('1.0','end')
            self.defn_area.config(state=DISABLED)
            self.txt_display.set(self.new_w)

    def recite_change_mode(self):
        if self.button_recitemode.cget('text') == '听音拼写':
            self.button_recitemode.config(text='看义拼写')
            self.defn_area.config(state=NORMAL)
            self.defn_area.insert('1.0', self.get_definition())
            self.defn_area.config(state=DISABLED)
        elif self.button_recitemode.cget('text') == '看义拼写':
            self.button_recitemode.config(text='听音拼写')
            self.defn_area.config(state=NORMAL)
            self.defn_area.delete('1.0', END)
            self.defn_area.config(state=DISABLED)
            Sound.play_mp3(self.new_w)

    def recite_afoot(self):
        self.recite_count = 0
        self.defn_area.config(state=NORMAL)
        self.defn_area.delete('1.0','end')
        if self.button_recitemode.cget('text') == '看义拼写':
            self.defn_area.insert('1.0', self.get_definition())
        self.defn_area.config(state=DISABLED)
        if self.button_recitemode.cget('text') == '听音拼写':
            Sound.play_mp3(self.new_w)

    def recite_judge(self):
        self.recite_count += 1
        if self.vocab_in.lower() == self.new_w:
            if self.button_no.cget('text') == '下一个':
                self.no_btn()
                return
            self.txt_display.set(self.new_w+' ✔')
            Sound.play_mp3(self.new_w)
            self.button_yes.config(state=NORMAL)
            self.recite_count = 0
        elif self.recite_count == 1:
            self.txt_display.set('wrong, try again')
            return
        elif self.recite_count == 2:
            self.txt_display.set('wrong, one last time')
            return
        elif self.recite_count >= 3:
            self.txt_display.set(self.new_w)
            Sound.play_mp3(self.new_w)
            # self.Entry_1.config(state=DISABLED)
            self.button_no.config(text='下一个')
        self.defn_area.config(state=NORMAL)
        self.defn_area.delete('1.0','end')
        self.defn_area.insert('1.0', self.def_after_judge)
        self.defn_area.config(state=DISABLED)

    # SR FUNCTION PACK # undone
    def sr_submit(self):
        if self.new_w:
            pass

test = VocabApp()
test.mainloop()
