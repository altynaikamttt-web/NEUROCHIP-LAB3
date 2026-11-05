"""NEURO•CHIP LAB 3 | Қазақ тіліндегі 3-сынып виртуалды зертханасы.
Авторлық интерактивті оқу демонстрациясы; кеңесші ережеге негізделген, LLM емес.
"""
import csv, json, os, random, subprocess, sys, threading, tkinter as tk
from pathlib import Path
from datetime import datetime
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk, ImageDraw

BASE = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
DATA = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'NeuroChipLab3'
RESULTS = DATA / 'results.json'
WHITE='#FFFFFF'; BG='#F1F7FF'; BLUE='#0869E8'; DARK='#10265C'; SOFT='#E6F0FF'; GREEN='#17A66C'; RED='#D83F59'; GOLD='#EAA526'
PARTS=[
 ('cpu','Процессор','Компьютердің «миы»: командаларды орындайды және ақпаратты өңдейді.','Компьютер есептеулерді орындай алмай қалды.','Қай құрылғы есептеулерді орындайды?'),
 ('ram','Жедел жад (RAM)','Қазір жұмыс істеп тұрған бағдарламалардың деректерін уақытша сақтайды.','Көп бағдарлама ашылғанда компьютер баяулады.','Қай құрылғы деректерді уақытша сақтайды?'),
 ('board','Аналық тақша','Компьютердің ішкі құрылғыларын өзара байланыстырады.','Құрылғылар бір-бірімен байланыса алмай тұр.','Қай құрылғы бөлшектерді байланыстырады?'),
 ('ssd','Жинақтауыш (SSD)','Файлдарды компьютер өшкеннен кейін де сақтайды.','Бұрын сақталған файлдарды таба алмай отырмыз.','Файлдар ұзақ уақыт қайда сақталады?'),
 ('psu','Қуат көзі','Компьютер бөлшектеріне электр қуатын жеткізеді.','Компьютер мүлдем қосылмай тұр.','Қай құрылғы электр қуатын береді?'),
]
PART = {p[0]:p for p in PARTS}
ALGORITHMS={
 'home':['Өз атыңды енгіз.','«Сабақты бастау» батырмасын бас.','Зерттеу, тәжірибе және тексеру бөлімдерін орында.'],
 'explore':['Компьютердің ішкі құрылғысын таңда.','Құрылғының атауы мен қызметін оқы немесе тыңда.','Бес құрылғыны зерттеп, «Ақауды тап» бөліміне өт.'],
 'diagnose':['Экрандағы ақау белгісін оқы.','Қай құрылғы жауапты екенін болжа.','Жауапты таңда, роботтың түсіндірмесін тыңда.','«Келесі тапсырма» арқылы бес жағдайды шеш.'],
 'assemble':['Төменгі сөреден бөлшекті тышқанмен ұстап ал.','Бөлшекті компьютер ішіндегі сәйкес орынға сүйреп апар.','Жасыл белгі шықса — дұрыс, қызыл белгі шықса — қайта көр.','Бес бөлшекті орнатып, «Тексеру» және «Іске қосу» батырмаларын бас.'],
 'quiz':['Сұрақты оқы.','Үш жауаптың біреуін таңда.','Түсіндірмені оқы, келесі сұраққа өт.','Бес сұрақтан кейін нәтижені қара.'],
 'mission':['Компьютердің мәселесін анықта.','Құрылғының қызметімен салыстыр.','Шешімді таңда және роботтың кері байланысын оқы.','Бес миссияны аяқтап, XP жина.'],
 'results':['Соңғы тапсырмалардың нәтижесін қара.','Қате болған тақырыпты анықта.','Сол бөлімге қайта оралып, қайталап орында.'],
 'teacher':['Оқушылардың сақталған нәтижелерін қара.','Қажет болса CSV файлына экспортта.','Нәтижелерді салыстырып, келесі сабаққа тапсырма жоспарла.'],
 'help':['Бөлімдердің орындалу ретін оқы.','Зертхананы «Басты беттен» баста.','Нақты компьютер корпусын мұғалімсіз ашпа.']
}
# Көрнекі модельдегі бөлшектердің жуық орналасуы (сурет 660x620).
HOTSPOTS={'cpu':(210,175,305,295),'ram':(345,125,455,315),'board':(125,110,435,395),'ssd':(305,405,475,555),'psu':(65,430,265,560)}
QUESTIONS=[
 ('Процессор не істейді?',['Файлды басып шығарады','Командаларды орындайды','Дыбыс шығарады'],1,'cpu'),
 ('Компьютер өшсе де файлды не сақтайды?',['Жедел жад','Процессор','SSD'],2,'ssd'),
 ('Жедел жадтың басты ерекшелігі қандай?',['Деректерді уақытша сақтайды','Электр қуатын береді','Экранды көрсетеді'],0,'ram'),
 ('Құрылғыларды не байланыстырады?',['Тінтуір','Аналық тақша','Принтер'],1,'board'),
 ('Қуат көзі не үшін керек?',['Электр қуатын жеткізуге','Файлдарды сақтауға','Сурет салуға'],0,'psu'),
]

class App:
 def __init__(self,root):
  self.root=root;root.title('NEURO•CHIP LAB 3 — Компьютерді құтқару миссиясы');root.geometry('1320x820');root.minsize(1050,690);root.configure(bg=BG)
  self.student=tk.StringVar(value='Оқушы');self.sound=tk.BooleanVar(value=False);self.full=tk.BooleanVar(value=False)
  self.page='home';self.xp=0;self.selected='cpu';self.step=0;self.answer_locked=False;self.answers=[];self.assembled=[];self.anim=0;self.session_saved=False;self.assembly_recorded=False
  self.photo=None;self.load_image();self.build_shell();self.navigate('home');self.animate()
 def load_image(self):
  try:
   im=Image.open(BASE/'assets'/'computer.png').convert('RGB');im=im.resize((580,545),Image.Resampling.LANCZOS);self.photo=ImageTk.PhotoImage(im)
  except Exception:self.photo=None
 def button(self,parent,text,fn,primary=False,width=None):
  return tk.Button(parent,text=text,command=fn,bg=BLUE if primary else WHITE,fg=WHITE if primary else DARK,activebackground='#D8E9FF',activeforeground=DARK,relief='flat',bd=0,highlightthickness=1,highlightbackground='#C8DDF8',font=('Segoe UI',11,'bold'),cursor='hand2',padx=13,pady=10,width=width)
 def label(self,parent,text,size=12,bold=False,color=DARK,bg=None,**kw):
  return tk.Label(parent,text=text,bg=bg or parent.cget('bg'),fg=color,font=('Segoe UI',size,'bold' if bold else 'normal'),**kw)
 def build_shell(self):
  head=tk.Frame(self.root,bg=WHITE,height=78);head.pack(fill='x');head.pack_propagate(False)
  self.label(head,'◈ NEURO•CHIP LAB 3',21,True,BLUE,bg=WHITE).pack(side='left',padx=24)
  self.label(head,'3-сынып  |  І тоқсан  |  Компьютердің ішкі құрылғылары',12,True,bg=WHITE).pack(side='left',padx=12)
  self.xplabel=self.label(head,'⭐ 0 XP',13,True,GOLD,bg=WHITE);self.xplabel.pack(side='right',padx=22)
  self.button(head,'🔊 Дыбыс',self.toggle_sound).pack(side='right',padx=4)
  self.button(head,'⛶ Толық экран',self.toggle_full).pack(side='right',padx=4)
  main=tk.Frame(self.root,bg=BG);main.pack(fill='both',expand=True)
  self.nav=tk.Frame(main,bg=WHITE,width=218);self.nav.pack(side='left',fill='y',padx=(12,0),pady=12);self.nav.pack_propagate(False)
  links=[('home','⌂  Басты бет'),('explore','🔬  Зертхана'),('diagnose','🩺  Ақауды тап'),('assemble','🧩  Құрастыру'),('quiz','☑  Тест'),('mission','🚀  Миссия'),('results','🏆  Нәтиже'),('teacher','📊  Мұғалім панелі'),('help','❔  Нұсқаулық')]
  for key,title in links:self.button(self.nav,title,lambda k=key:self.navigate(k)).pack(fill='x',padx=10,pady=5)
  self.content=tk.Frame(main,bg=BG);self.content.pack(side='left',fill='both',expand=True,padx=14,pady=12)
  foot=tk.Frame(self.root,bg=WHITE,height=34);foot.pack(fill='x');self.status=self.label(foot,'Виртуалды зертхана: нақты компьютерді ересексіз ашпа!',10,color='#526586',bg=WHITE);self.status.pack(side='left',padx=20)
  self.robot=tk.Canvas(foot,width=90,height=30,bg=WHITE,highlightthickness=0);self.robot.pack(side='right',padx=14)
 def clear(self):
  for w in self.content.winfo_children():w.destroy()
 def title(self,text,subtitle=''):
  self.label(self.content,text,22,True,BLUE).pack(anchor='w',pady=(0,5))
  if subtitle:self.label(self.content,subtitle,11,color='#536783',wraplength=940,justify='left').pack(anchor='w',pady=(0,8))
  steps=ALGORITHMS.get(self.page,[])
  if steps:
   panel=tk.Frame(self.content,bg='#E4F2FF',highlightbackground='#B4D9FA',highlightthickness=1,padx=10,pady=7)
   panel.pack(fill='x',pady=(0,10))
   self.label(panel,'🧭 Орындау алгоритмі',11,True,BLUE,bg='#E4F2FF').pack(anchor='w')
   self.label(panel,'  →  '.join(f'{i}. {step}' for i,step in enumerate(steps,1)),10,bg='#E4F2FF',wraplength=920,justify='left').pack(anchor='w',pady=(3,0))
 def card(self,parent=None):
  f=tk.Frame(parent or self.content,bg=WHITE,highlightbackground='#D4E4F9',highlightthickness=1,padx=16,pady=16);return f
 def navigate(self,page):
  self.page=page;self.clear();self.status.config(text='NEURO: «Байқа, ойлан, тәжірибе жаса!»')
  getattr(self,'show_'+page)()
 def speak(self,text):
  if not self.sound.get():return
  if sys.platform!='win32':self.status.config(text='Дыбыстау Windows жүйесінде жұмыс істейді.');return
  def work():
   try:
    s=text.replace("'","''")[:550]
    cmd="Add-Type -AssemblyName System.Speech; $v=New-Object System.Speech.Synthesis.SpeechSynthesizer; $v.Speak('"+s+"')"
    subprocess.run(['powershell','-NoProfile','-NonInteractive','-Command',cmd],timeout=30,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
   except Exception:pass
  threading.Thread(target=work,daemon=True).start()
 def toggle_sound(self):
  self.sound.set(not self.sound.get());self.status.config(text='Дыбыс қосылды' if self.sound.get() else 'Дыбыс өшірілді')
  if self.sound.get():self.speak('Сәлем! Мен Нейро. Зертханаға қош келдің!')
 def toggle_full(self):self.full.set(not self.full.get());self.root.attributes('-fullscreen',self.full.get())
 def show_home(self):
  self.title('Қош келдің, жас зерттеуші! 🤖','Компьютердің ішкі әлемін аш: құрылғыларды зертте, ақауды анықта және миссияны орында.')
  top=self.card();top.pack(fill='x',pady=10)
  self.label(top,'Оқушының аты',12,True).pack(side='left',padx=10)
  tk.Entry(top,textvariable=self.student,font=('Segoe UI',13),width=25,relief='solid',bd=1).pack(side='left',padx=8)
  self.button(top,'▶ Сабақты бастау',lambda:self.navigate('explore'),True).pack(side='left',padx=14)
  self.label(top,'Офлайн • Қазақ тілінде',11,color=GREEN,bg=WHITE).pack(side='right',padx=12)
  body=self.card();body.pack(fill='both',expand=True,pady=12)
  self.label(body,'NEURO миссиясы',20,True,BLUE,bg=WHITE).pack(anchor='w',pady=8)
  self.label(body,'Компьютердің 5 маңызды ішкі құрылғысын танып, оларды дұрыс қолдануды үйрен.\nӘр бөлімде жаңа тапсырма мен ақылды түсіндірме күтеді!',15,bg=WHITE,justify='left').pack(anchor='w',pady=12)
  for key,text in [('explore','🔬 Құрылғыларды зерттеу'),('diagnose','🩺 Ақауды анықтау'),('assemble','🧩 Компьютерді құрастыру'),('quiz','☑ Білімді тексеру'),('mission','🚀 Құтқару миссиясы')]:self.button(body,text,lambda k=key:self.navigate(k)).pack(anchor='w',fill='x',pady=5)
 def computer(self,parent):
  frame=tk.Frame(parent,bg=WHITE);frame.pack(side='left',fill='both',expand=True)
  canvas=tk.Canvas(frame,width=600,height=570,bg=WHITE,highlightthickness=0);canvas.pack(expand=True)
  if self.photo:canvas.create_image(10,8,image=self.photo,anchor='nw')
  else:canvas.create_rectangle(30,25,565,540,fill='#D7E9FC',outline=BLUE,width=3)
  # Түймелер суреттің үстіне орналастырылған; көрнекі аймақты таңдауға болады.
  spots={'cpu':(220,175),'ram':(400,185),'board':(130,325),'ssd':(410,475),'psu':(115,475)}
  for key,(x,y) in spots.items():
   name=PART[key][1];short={'cpu':'CPU','ram':'RAM','board':'BOARD','ssd':'SSD','psu':'PSU'}[key]
   ident=canvas.create_oval(x-21,y-21,x+21,y+21,fill=GOLD if self.selected==key else BLUE,outline=WHITE,width=3,tags=(key,))
   canvas.create_text(x,y,text=short,fill=WHITE,font=('Segoe UI',9,'bold'),tags=(key,))
   canvas.tag_bind(key,'<Button-1>',lambda e,k=key:self.pick(k));canvas.tag_bind(key,'<Enter>',lambda e:canvas.config(cursor='hand2'));canvas.tag_bind(key,'<Leave>',lambda e:canvas.config(cursor=''))
  self.pc_canvas=canvas
 def pick(self,key):
  self.selected=key
  if self.page=='explore':self.update_explore()
  elif self.page=='assemble':self.place_part(key)
 def show_explore(self):
  self.title('🔬 Құрылғыларды зерттеу','Суреттегі көк дөңгелектерді немесе құрылғы атауларын бас. Робот олардың қызметін түсіндіреді.')
  area=self.card();area.pack(fill='both',expand=True)
  self.computer(area)
  side=tk.Frame(area,bg=WHITE,width=315);side.pack(side='right',fill='y',padx=8);side.pack_propagate(False)
  self.part_title=self.label(side,'',18,True,BLUE,bg=WHITE,wraplength=295);self.part_title.pack(anchor='w',pady=12)
  self.part_info=self.label(side,'',13,bg=WHITE,wraplength=290,justify='left');self.part_info.pack(anchor='w',pady=9)
  self.button(side,'🔊 Тыңдау',lambda:self.speak(PART[self.selected][1]+'. '+PART[self.selected][2]),True).pack(fill='x',pady=8)
  for key in PART:self.button(side,PART[key][1],lambda k=key:self.pick(k)).pack(fill='x',pady=3)
  self.button(side,'Келесі: Ақауды тап →',lambda:self.navigate('diagnose'),True).pack(fill='x',pady=12)
  self.update_explore()
 def update_explore(self):
  p=PART[self.selected];self.part_title.config(text=p[1]);self.part_info.config(text=p[2]+'\n\n🤖 NEURO: «Құрылғының міндетін есіңде сақта!»')
  if hasattr(self,'pc_canvas') and self.pc_canvas.winfo_exists():
   for key in PART:
    for item in self.pc_canvas.find_withtag(key):
     if self.pc_canvas.type(item)=='oval':self.pc_canvas.itemconfigure(item,fill=GOLD if key==self.selected else BLUE)
  self.speak(p[1]+'. '+p[2])
 def reset_activity(self,kind):self.step=0;self.answers=[];self.answer_locked=False;self.activity=kind;self.show_activity()
 def show_diagnose(self):self.reset_activity('diagnose')
 def show_quiz(self):self.reset_activity('quiz')
 def show_mission(self):self.reset_activity('mission')
 def show_activity(self):
  self.clear();kind=self.activity
  if self.step>=5:self.finish_activity();return
  names={'diagnose':'🩺 Ақауды анықтау','quiz':'☑ Білімді тексеру','mission':'🚀 Құтқару миссиясы'}
  self.title(f'{names[kind]} • {self.step+1}/5','Жауапты таңда. NEURO дұрыс немесе қате екенін түсіндіреді.')
  key=PARTS[self.step][0] if kind!='quiz' else QUESTIONS[self.step][3]
  p=PART[key]
  q=QUESTIONS[self.step] if kind=='quiz' else (p[4],None,None,key)
  box=self.card();box.pack(fill='both',expand=True,pady=6)
  if kind!='quiz':self.label(box,'⚠ '+p[3],16,True,RED,bg=WHITE,wraplength=830).pack(anchor='w',pady=14)
  self.label(box,q[0],18,True,bg=WHITE,wraplength=850,justify='left').pack(anchor='w',pady=15)
  choices=q[1] if kind=='quiz' else [p[1]]+[PART[k][1] for k in PART if k!=key][:2]
  if kind!='quiz':random.Random(self.step+5).shuffle(choices)
  self.choice_buttons=[]
  for i,option in enumerate(choices):
   b=self.button(box,f'{chr(65+i)}. {option}',lambda opt=option:self.submit_answer(opt));b.pack(fill='x',pady=7);self.choice_buttons.append(b)
  self.feedback=self.label(box,'🤖 NEURO: Ойланып жауап бер!',13,color=BLUE,bg=WHITE,wraplength=860,justify='left');self.feedback.pack(anchor='w',pady=17)
  self.nextbtn=self.button(box,'Келесі тапсырма →',self.next_activity,True)
  self.current_options=choices;self.current_key=key;self.answer_locked=False
 def submit_answer(self,choice):
  if self.answer_locked:return
  correct=PART[self.current_key][1] if self.activity!='quiz' else QUESTIONS[self.step][1][QUESTIONS[self.step][2]]
  ok=choice==correct;self.answer_locked=True
  if ok:self.xp+=20;self.xplabel.config(text=f'⭐ {self.xp} XP')
  explanation=PART[self.current_key][2]
  msg=('Дұрыс! +20 XP. ' if ok else f'Қазір дұрыс емес. Дұрыс жауап: {correct}. ')+explanation
  self.feedback.config(text='🤖 NEURO: '+msg,fg=GREEN if ok else RED);self.speak(msg)
  for b in self.choice_buttons:b.config(state='disabled',bg=SOFT)
  self.answers.append({'question':self.step+1,'choice':choice,'correct':ok,'topic':PART[self.current_key][1]})
  self.nextbtn.pack(anchor='e',pady=12)
 def next_activity(self):self.step+=1;self.show_activity()
 def finish_activity(self):
  kind=self.activity;correct=sum(x['correct'] for x in self.answers)
  self.clear();self.title('🏆 Миссия аяқталды!',f'{correct} / 5 дұрыс жауап • осы бөлімнен {correct*20} XP')
  box=self.card();box.pack(fill='x',pady=15)
  self.label(box,'Жарайсың, '+(self.student.get().strip() or 'Оқушы')+'!',21,True,BLUE,bg=WHITE).pack(pady=18)
  self.label(box,f'Нәтиже: {correct*20}/100 ұпай',17,bg=WHITE).pack(pady=8)
  self.save_result(kind,correct)
  self.button(box,'Қайта ойнау',lambda:self.reset_activity(kind),True).pack(pady=12)
  self.button(box,'Нәтижелер',lambda:self.navigate('results')).pack(pady=6)
 def show_assemble(self):
  self.assembled=[];self.assembly_recorded=False;self.assembly_awarded=set();self.drag_key=None;self.drag_origin=None
  self.render_assemble()
 def render_assemble(self):
  self.clear();self.title('🧩 Құрастыру зертханасы — сүйреп орналастыр','Бөлшектерді төменгі сөреден тышқанмен ұстап, компьютер ішіндегі сәйкес ұяшыққа апар.')
  shell=self.card();shell.pack(fill='both',expand=True)
  main=tk.Frame(shell,bg=WHITE);main.pack(fill='both',expand=True)
  left=tk.Frame(main,bg=WHITE);left.pack(side='left',fill='both',expand=True)
  self.assembly_canvas=tk.Canvas(left,width=735,height=515,bg='#F7FBFF',highlightthickness=1,highlightbackground='#BFD9F8')
  self.assembly_canvas.pack(fill='both',expand=True)
  right=tk.Frame(main,bg=WHITE,width=230);right.pack(side='right',fill='y',padx=(12,0));right.pack_propagate(False)
  self.label(right,'🤖 NEURO кеңесшісі',15,True,BLUE,bg=WHITE,wraplength=220).pack(anchor='w',pady=(2,8))
  self.assembly_feedback=self.label(right,'Бөлшекті тышқанмен ұстап, сәйкес орынға сүйре. Қателессең, қайта көр!',12,bg=WHITE,wraplength=210,justify='left')
  self.assembly_feedback.pack(anchor='w',pady=8)
  self.assembly_status=self.label(right,'',13,True,BLUE,bg=WHITE,wraplength=210,justify='left');self.assembly_status.pack(anchor='w',pady=12)
  self.button(right,'✓ Тексеру',self.check_assembly,True).pack(fill='x',pady=5)
  self.button(right,'⏻ Іске қосу',self.start_computer).pack(fill='x',pady=5)
  self.button(right,'↻ Қайта бастау',lambda:self.navigate('assemble')).pack(fill='x',pady=5)
  self.button(right,'🔊 Нұсқауды тыңдау',lambda:self.speak('Бөлшекті төменгі сөреден ұстап, компьютер ішіндегі сәйкес орынға апар.')).pack(fill='x',pady=5)
  self.assembly_canvas.bind('<ButtonPress-1>',self.assembly_press)
  self.assembly_canvas.bind('<B1-Motion>',self.assembly_move)
  self.assembly_canvas.bind('<ButtonRelease-1>',self.assembly_release)
  self.draw_assembly()
 def assembly_layout(self):
  # Барлық координаталар 735 × 515 логикалық кенепке қатысты.
  return {'board':(104,94,465,348),'cpu':(200,135,286,212),'ram':(330,129,397,249),'ssd':(315,271,428,328),'psu':(114,268,241,334)}
 def draw_assembly(self):
  c=self.assembly_canvas;c.delete('all')
  c.create_text(18,16,text='ВИРТУАЛДЫ ЖҮЙЕЛІК БЛОК',anchor='nw',fill=DARK,font=('Segoe UI',13,'bold'))
  # Корпус және көлем әсерін беретін бірнеше қабат
  c.create_polygon(86,79,468,79,495,99,495,370,468,351,86,351,fill='#D9E7F6',outline='#617B9F',width=2)
  c.create_rectangle(86,79,468,351,fill='#182B46',outline='#536B8B',width=5)
  c.create_rectangle(102,94,453,338,fill='#173D61',outline='#50A8F2',width=2)
  for x in range(118,453,33):c.create_line(x,97,x,337,fill='#1B5279',width=1)
  for y in range(107,338,33):c.create_line(105,y,450,y,fill='#1B5279',width=1)
  c.create_oval(407,105,449,147,fill='#20385B',outline='#4FD5FF',width=3)
  c.create_oval(417,115,439,137,fill='#55D7F5',outline='#174A6D',width=2)
  c.create_text(278,367,text='Сәйкес ұяшыққа апар',fill='#41617F',font=('Segoe UI',10))
  for key,(x1,y1,x2,y2) in self.assembly_layout().items():
   if key=='board' and key in self.assembled:
    c.create_rectangle(x1,y1,x2,y2,fill='#174F73',outline='#29D2A2',width=3)
    for x in range(x1+18,x2-10,28):c.create_line(x,y1+12,x,y2-12,fill='#2E8B8D')
   if key=='board' and key not in self.assembled:
    c.create_rectangle(x1,y1,x2,y2,fill='#1E4968',outline='#8BC6FA',width=2,dash=(7,4))
   if key!='board':
    installed=key in self.assembled
    c.create_rectangle(x1,y1,x2,y2,fill='#176D67' if installed else '#284D6C',outline='#38E5AD' if installed else '#70C4FF',width=3,dash=() if installed else (6,4))
   if key!='board' or key not in self.assembled:
    c.create_text((x1+x2)/2,(y1+y2)/2,text=('✓ ' if key in self.assembled else '＋ ')+{'cpu':'CPU','ram':'RAM','board':'АНАЛЫҚ ТАҚША','ssd':'SSD','psu':'ҚУАТ КӨЗІ'}[key],fill='white',font=('Segoe UI',9,'bold'),width=x2-x1-8)
  # Бөлшектер сөреде тұрады; әрбір бөлшектің өзіне тән сызбасы бар.
  c.create_rectangle(10,389,724,504,fill='#E8F3FF',outline='#A8CFF6',width=2)
  c.create_text(20,398,text='БӨЛШЕКТЕР СӨРЕСІ  •  Сүйреп апар ↓',anchor='nw',fill=BLUE,font=('Segoe UI',10,'bold'))
  self.tray={}
  for i,(key,name,*_) in enumerate(PARTS):
   x=17+i*143;y=427;self.tray[key]=(x,y,x+133,y+68)
   done=key in self.assembled
   c.create_rectangle(x,y,x+133,y+68,fill='#D7E7F3' if done else WHITE,outline='#A5BCD6' if done else BLUE,width=2,tags=('tray_'+key,))
   if key=='cpu':
    c.create_rectangle(x+10,y+10,x+46,y+44,fill='#C4D2DF',outline='#62758C',width=3)
    for d in range(0,5):c.create_line(x+14+d*7,y+7,x+14+d*7,y+10,fill=GOLD,width=2)
   elif key=='ram':
    c.create_rectangle(x+9,y+17,x+49,y+36,fill='#1F9A64',outline='#176B48',width=2)
    for d in range(4):c.create_rectangle(x+13+d*9,y+20,x+19+d*9,y+31,fill='#1C3140')
   elif key=='board':
    c.create_rectangle(x+12,y+8,x+48,y+45,fill='#237BA1',outline='#124E7D',width=2)
    c.create_rectangle(x+22,y+17,x+36,y+31,fill='#B3C4CF')
   elif key=='ssd':
    c.create_rectangle(x+10,y+12,x+49,y+42,fill='#3B4C62',outline='#0F263E',width=2)
    c.create_text(x+29,y+27,text='SSD',fill='white',font=('Segoe UI',9,'bold'))
   else:
    c.create_rectangle(x+10,y+9,x+48,y+44,fill='#414C5C',outline='#202C39',width=2)
    c.create_oval(x+17,y+15,x+41,y+39,outline='#E3AD45',width=3)
   c.create_text(x+72,y+26,text={'cpu':'CPU','ram':'RAM','board':'Тақша','ssd':'SSD','psu':'PSU'}[key],anchor='w',fill='#6A7D93' if done else DARK,font=('Segoe UI',10,'bold'))
   c.create_text(x+66,y+53,text='Орнатылды ✓' if done else 'Сүйреп апар',fill=GREEN if done else '#4D6A89',font=('Segoe UI',9))
  self.assembly_status.config(text=f'Орнатылған: {len(self.assembled)} / 5')
 def assembly_press(self,event):
  x,y=event.x,event.y
  for key,(x1,y1,x2,y2) in self.tray.items():
   if x1<=x<=x2 and y1<=y<=y2 and key not in self.assembled:
    self.drag_key=key;self.drag_origin=(x,y);self.draw_drag_ghost(x,y);return
  self.drag_key=None
 def draw_drag_ghost(self,x,y):
  c=self.assembly_canvas;c.delete('drag')
  if not self.drag_key:return
  c.create_rectangle(x-61,y-23,x+61,y+23,fill='#FFF3C4',outline='#E2A51B',width=3,tags='drag')
  c.create_text(x,y,text=PART[self.drag_key][1],font=('Segoe UI',10,'bold'),fill=DARK,width=116,tags='drag')
 def assembly_move(self,event):
  if self.drag_key:self.draw_drag_ghost(event.x,event.y)
 def assembly_release(self,event):
  key=self.drag_key
  if not key:return
  self.drag_key=None;self.assembly_canvas.delete('drag')
  x,y=event.x,event.y;target=None
  # Кіші ұяшықтарға басымдық беріледі, өйткені олар аналық тақшаның үстінде.
  for k in ('cpu','ram','ssd','psu','board'):
   x1,y1,x2,y2=self.assembly_layout()[k]
   if x1<=x<=x2 and y1<=y<=y2:target=k;break
  if target==key:
   self.assembled.append(key)
   if key not in self.assembly_awarded:
    self.xp+=20;self.assembly_awarded.add(key);self.xplabel.config(text=f'⭐ {self.xp} XP')
   self.assembly_feedback.config(text='✅ Дұрыс! '+PART[key][1]+' орнатылды. '+PART[key][2],fg=GREEN)
   self.speak('Дұрыс! '+PART[key][1]+' орнатылды.')
   self.draw_assembly();self.assembly_flash(key,True)
  else:
   self.assembly_feedback.config(text='❌ Бұл орын сәйкес келмейді. '+PART[key][1]+' үшін дұрыс ұяшықты тап!',fg=RED)
   self.draw_assembly();self.assembly_flash(target,False)
 def assembly_flash(self,key,success):
  if not key:return
  c=self.assembly_canvas;x1,y1,x2,y2=self.assembly_layout()[key]
  outline=GREEN if success else RED
  item=c.create_rectangle(x1-3,y1-3,x2+3,y2+3,outline=outline,width=6,tags='flash')
  def blink(n):
   if not c.winfo_exists():return
   if n>=6:c.delete('flash');return
   c.itemconfigure(item,state='normal' if n%2==0 else 'hidden');c.after(150,lambda:blink(n+1))
  blink(0)
 def check_assembly(self):
  missing=[p[1] for p in PARTS if p[0] not in self.assembled]
  if missing:
   self.assembly_feedback.config(text=f'🔎 Әлі {len(missing)} бөлшек жетіспейді: '+', '.join(missing)+'.',fg=RED)
   self.speak('Әлі '+str(len(missing))+' бөлшек жетіспейді.')
  else:
   self.assembly_feedback.config(text='🏆 Тамаша! Бес құрылғы да дұрыс орнатылған. Енді «Іске қосу» батырмасын бас.',fg=GREEN)
   self.speak('Тамаша! Барлық бөлшек орнатылды.')
 def start_computer(self):
  if len(self.assembled)<5:
   self.check_assembly();return
  if not self.assembly_recorded:
   self.save_result('assemble',5);self.assembly_recorded=True
  self.assembly_feedback.config(text='🚀 Компьютер іске қосылды! Миссия сәтті аяқталды. +100 XP жиналды.',fg=GREEN)
  self.assembly_canvas.create_text(275,61,text='✓ ЖҮЙЕ ДАЙЫН!',fill=GREEN,font=('Segoe UI',19,'bold'),tags='boot')
  self.speak('Құттықтаймын! Компьютер іске қосылды. Миссия аяқталды.')
 def load_results(self):
  try:
   if RESULTS.exists():
    with RESULTS.open(encoding='utf-8') as f:r=json.load(f)
    return r if isinstance(r,list) else []
  except (OSError,ValueError):pass
  return []
 def save_result(self,kind,correct):
  r=self.load_results();r.append({'name':self.student.get().strip()[:70] or 'Оқушы','date':datetime.now().strftime('%Y-%m-%d %H:%M'),'activity':kind,'correct':correct,'total':5,'xp':self.xp,'answers':self.answers if kind!='assemble' else []})
  try:DATA.mkdir(parents=True,exist_ok=True);RESULTS.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');self.status.config(text='Нәтиже сақталды ✓')
  except OSError as e:messagebox.showwarning('Сақтау қатесі',str(e))
 def show_results(self):
  self.title('🏆 Менің нәтижелерім','Осы компьютерде сақталған барлық оқу әрекеттері.')
  self.show_table(self.load_results(),teacher=False)
 def show_teacher(self):
  self.title('📊 Мұғалім панелі','Оқушылардың нәтижелері жергілікті компьютерде сақталады. Жеке деректерді рұқсатсыз таратпаңыз.')
  self.show_table(self.load_results(),teacher=True)
 def show_table(self,rows,teacher):
  box=self.card();box.pack(fill='both',expand=True)
  tree=ttk.Treeview(box,columns=('date','name','activity','correct','xp'),show='headings',height=16)
  for k,t,w in [('date','Күні',150),('name','Оқушы',170),('activity','Бөлім',130),('correct','Дұрыс',80),('xp','XP',75)]:tree.heading(k,text=t);tree.column(k,width=w)
  for r in reversed(rows):tree.insert('','end',values=(r.get('date',''),r.get('name',''),r.get('activity',''),f"{r.get('correct',0)}/{r.get('total',5)}",r.get('xp',0)))
  tree.pack(fill='both',expand=True)
  if teacher:
   self.button(box,'CSV экспорттау',lambda:self.export(rows),True).pack(side='left',pady=12)
   self.button(box,'Нәтижелер папкасын ашу',self.open_folder).pack(side='left',padx=12,pady=12)
 def export(self,rows):
  filename=filedialog.asksaveasfilename(defaultextension='.csv',filetypes=[('CSV','*.csv')],initialfile='NEUROCHIP_results.csv')
  if not filename:return
  try:
   with open(filename,'w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f,delimiter=';');w.writerow(['Күні','Оқушы','Бөлім','Дұрыс','Барлығы','XP'])
    for r in rows:w.writerow([r.get(x,'') for x in ['date','name','activity','correct','total','xp']])
   messagebox.showinfo('Дайын','CSV файлы сақталды!')
  except OSError as e:messagebox.showerror('Қате',str(e))
 def open_folder(self):
  DATA.mkdir(parents=True,exist_ok=True)
  if sys.platform=='win32':os.startfile(str(DATA))
  else:messagebox.showinfo('Нәтижелер',str(DATA))
 def show_help(self):
  self.title('❔ Нұсқаулық және жоба туралы')
  box=self.card();box.pack(fill='both',expand=True)
  content=('Әр бөлімнің жоғарғы жағында «Орындау алгоритмі» берілген.\n\n'
           '1. «Зертхана» — компьютердің ішкі құрылғыларын таңда және олардың қызметін тыңда.\n\n'
           '2. «Ақауды тап» — компьютердегі ақаудың белгісін оқып, жауап бер.\n\n'
           '3. «Құрастыру» — бөлшектерді тышқанмен сүйреп, сәйкес ұяшықтарға орналастыр; тексер және іске қос.\n\n'
           '4. «Тест» және «Миссия» — біліміңді тексер, XP жина.\n\n'
           '5. «Мұғалім панелі» — нәтижелерді қара және CSV-ге шығар.\n\n'
           'Дыбыс Windows жүйесінің дауыстау мүмкіндігіне тәуелді.\n'
           'NEURO кеңесшісі — ережеге негізделген түсіндіру алгоритмі, нейрожелі емес.\n'
           'Бұл оқу симуляторы: нақты компьютерді ашу/жөндеу нұсқаулығы емес.\n'
           'Esc пернесі толық экраннан шығарады.')
  self.label(box,content,13,bg=WHITE,justify='left',wraplength=850).pack(anchor='nw',pady=15)
 def animate(self):
  self.anim+=1
  if self.robot.winfo_exists():
   c=self.robot;c.delete('all');dy=2 if self.anim%8<4 else 0
   c.create_oval(21,3+dy,65,27+dy,fill='#0B79ED',outline='#42CBFF',width=2)
   c.create_oval(31,12+dy,37,17+dy,fill='white',outline='');c.create_oval(49,12+dy,55,17+dy,fill='white',outline='')
   c.create_arc(37,13+dy,50,23+dy,start=190,extent=160,style='arc',outline='white',width=2)
  self.root.after(240,self.animate)

if __name__=='__main__':
 root=tk.Tk();app=App(root);root.bind('<Escape>',lambda e:(app.full.set(False),root.attributes('-fullscreen',False)));root.mainloop()
