# -*- coding: utf-8 -*-
import midiate
import tkinter
from tkinter import font


def choose_input():
    inputs = midiate.enum_input()
    def f(x):
        if x in inputs: return x
    return (f('MPKmini2') or f('USB Oxygen 8 v2') or f('A-500S') or f('loopMIDI port') or
            inputs[0])

def choose_output():
    outputs = midiate.enum_output()
    def f(x):
        if x in outputs: return x
    return (f('CASIO USB-MIDI') or f('Microsoft GS Wavetable Synth') or
            outputs[0])

def open_input():
    return midiate.open_input(name=choose_input());

def open_output():
    return midiate.open_output(name=choose_output());

def open_both_io():
    return open_input(),open_output()


class Application(tkinter.Frame):

    def __init__(self, master=None):
        super().__init__(master)
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        font0 = font.Font(family='Consolas', size=14, weight='bold')
        self.label = tkinter.Label(self, text='' , fg='darkSlateGray', font=font0)
        self.label.pack()
        self.quit = tkinter.Button(self, text="終了しま～す！",
                                   bg='white',
                                   command=self.master.destroy)
        self.quit.pack()
        font1 = font.Font(family='Helvetica', size=18, weight='bold')
        self.statusLabel = tkinter.Label(self, text="", font=font1)
        self.statusLabel.pack()

    def say_hi(self):
        print("hi there, everyone!")

statusLabel = None
def status(text):
    statusLabel.config(text=text)

def wait(title="MIDI信号処理デモ",text=""):
    root = tkinter.Tk()
    root.geometry("600x200")
    root.title(title)
    app = Application(master=root)
    app.label.config(text=text)
    global statusLabel
    statusLabel = app.statusLabel
    app.mainloop()
