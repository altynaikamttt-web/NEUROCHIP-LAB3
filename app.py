"""NEURO•CHIP LAB 3 — offline grade-3 computer components lab.
The robot gives rule-based feedback; it is not a generative AI model.
"""
import csv, json, os, random, sqlite3, sys, threading, subprocess, base64
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk

BASE=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent))
DATA=Path(os.environ.get('LOCALAPPDATA',str(Path.home()))) / 'NeuroChipLab3'
DATA.mkdir(parents=True,exist_ok=True)
DB=DATA/'progress.sqlite3'
BG='#F2F6FD'; WHITE='#FFFFFF'; NAVY='#172C53'; BLUE='#1463D7'; GREEN='#087E57'; RED='#BC3047'; SOFT='#E8F0FC'
PARTS=[
 ('board','Аналық тақша','Компьютердің барлық ішкі құрылғыларын өзара байланыстырады.','Құрылғылар бір-бірімен байланыспай қалды.'),
 ('cpu','Процессор (CPU)','Командаларды орындайды, есептеулер жүргізеді. Оны компьютердің «миы» деп атайды.','Компьютер есептеулерді орындай алмай тұр.'),
 ('ram','Жедел жад (RAM)','Жұмыс істеп тұрған бағдарламалардың деректерін уақытша сақтайды.','Бірнеше бағдарлама ашылғанда жұмыс баяулады.'),
 ('ssd','Жинақтауыш (SSD)','Файлдар мен бағдарламаларды компьютер сөнгенде де сақтайды.','Сақталған файлдар ашылмай қалды.'),
 ('psu','Қуат көзі (PSU)','Компьютер бөлшектеріне қажетті электр қуатын жеткізеді.','Компьютер мүлде қосылмай қалды.')]
P={x[0]:x for x in PARTS}
QUESTIONS=[('Компьютердің «миы» қай құрылғы?','cpu'),('Қай құрылғы деректерді уақытша сақтайды?','ram'),('Қай құрылғы басқа бөлшектерді байланыстырады?','board'),('Файлдар компьютер өшсе де қайда сақталады?','ssd'),('Электр қуатын қай құрылғы жеткізеді?','psu')]

DETAILS={
 'board':('Не үшін керек?', 'Аналық тақша — компьютердің негізгі үлкен платасы. Процессор, жедел жад, жинақтауыш және басқа құрылғылар осы тақшаға қосылады.', 'Қайда орналасады?', 'Жүйелік блок корпусының ішіндегі ең үлкен тікбұрышты тақша. Алдымен оны корпусқа бекітеді.', 'Есте сақта:', 'Аналық тақша — барлық құрылғыны біріктіретін ортақ жол.'),
 'cpu':('Не үшін керек?', 'Процессор (CPU) командаларды өңдейді, есептейді және бағдарламалардың орындалуын басқарады. Жылдам жұмыс істеуіне оның мүмкіндіктері әсер етеді.', 'Қайда орналасады?', 'Аналық тақшадағы арнайы процессор ұясына орнатылады. Әдетте оның үстіне салқындатқыш бекітіледі.', 'Есте сақта:', 'Процессор — есептеулерді орындайтын басқарушы құрылғы.'),
 'ram':('Не үшін керек?', 'Жедел жад (RAM) компьютер дәл қазір пайдаланып жатқан ақпаратты уақытша ұстайды. Компьютер өшкенде жедел жадтағы деректер сақталмайды.', 'Қайда орналасады?', 'Аналық тақшадағы ұзынша RAM слотына салынады. Оны SSD жинақтауышымен шатастырма.', 'Есте сақта:', 'RAM — уақытша жад, ал SSD — ұзақ мерзімді сақтау орны.'),
 'ssd':('Не үшін керек?', 'SSD — файлдарды, суреттерді, ойындар мен операциялық жүйені сақтайтын жинақтауыш. Компьютер сөнгеннен кейін де ақпарат сақталады.', 'Қайда орналасады?', 'Бұл виртуалды үлгіде SSD корпус ішіндегі төменгі сақтау орнына орнатылады. Нақты компьютерде SSD түріне қарай аналық тақшаға да орнатылуы мүмкін.', 'Есте сақта:', 'SSD — тұрақты сақтау құрылғысы.'),
 'psu':('Не үшін керек?', 'Қуат көзі (PSU) электр желісінен келетін қуатты компьютердің ішкі бөлшектеріне қажетті түрге айналдырып жеткізеді.', 'Қайда орналасады?', 'Жүйелік блоктың төменгі сол жақ бөлігіндегі арнайы орынға орнатылады.', 'Есте сақта:', 'Қуат көзі болмаса компьютер қосылмайды. Нақты электр құрылғыларын өз бетіңше ашпа.')
}
# Drawing coordinates use a 720×460 reference surface; scaled with canvas dimensions.
ZONES={'board':(145,65,565,390),'cpu':(280,135,365,220),'ram':(395,125,455,275),'ssd':(485,315,605,380),'psu':(40,325,175,410)}
ORDER=['board','cpu','ram','ssd','psu']

def connect():
 c=sqlite3.connect(DB)
 c.execute('CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY, student TEXT NOT NULL, class_name TEXT NOT NULL, started TEXT NOT NULL, finished TEXT, score INTEGER DEFAULT 0, mistakes INTEGER DEFAULT 0, attempts INTEGER DEFAULT 0, explored INTEGER DEFAULT 0, assembled INTEGER DEFAULT 0, quiz_correct INTEGER DEFAULT 0, diagnosis_correct INTEGER DEFAULT 0, status TEXT DEFAULT "Орындалуда")')
 c.execute('CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, session_id INTEGER, time TEXT, section TEXT, question TEXT, answer TEXT, correct INTEGER, FOREIGN KEY(session_id) REFERENCES sessions(id))')
 c.commit();return c

class App:
 def __init__(self,root):
  self.root=root;root.title('NEURO•CHIP LAB 3 — Оқушы зертханасы және мұғалім панелі');root.geometry('1220x800');root.minsize(940,630);root.configure(bg=BG)
  self.name=tk.StringVar();self.class_name=tk.StringVar(value='3-сынып');self.sound=tk.BooleanVar(value=False)
  self.session=None;self.score=0;self.mistakes=0;self.attempts=0;self.explored=set();self.placed=set();self.credited=set();self.quiz_done=set();self.diagnose_done=set();self.selected=None;self.drag_key=None;self.mode='student';self.page='login';self.photo=None;self.speech_token=0
  self.shell();self.login()
 def label(self,p,t,size=12,bold=False,color=NAVY,**kw):return tk.Label(p,text=t,font=('Segoe UI',size,'bold' if bold else 'normal'),bg=p.cget('bg'),fg=color,**kw)
 def btn(self,p,t,fn,primary=False):return tk.Button(p,text=t,command=fn,font=('Segoe UI',11,'bold'),bg=BLUE if primary else WHITE,fg=WHITE if primary else NAVY,activebackground='#CDE1FC',relief='solid',bd=1,highlightthickness=0,cursor='hand2',padx=12,pady=9)
 def shell(self):
  self.header=tk.Frame(self.root,bg=WHITE,height=67);self.header.pack(fill='x');self.header.pack_propagate(False)
  self.label(self.header,'◈ NEURO•CHIP LAB 3',19,True,BLUE).pack(side='left',padx=18)
  self.scorelabel=self.label(self.header,'⭐ 0 ұпай | ❌ 0 қате',11,True);self.scorelabel.pack(side='right',padx=16)
  self.btn(self.header,'🔊 Дыбыс: өшірулі',self.toggle_sound).pack(side='right',padx=5)
  self.body=tk.Frame(self.root,bg=BG);self.body.pack(fill='both',expand=True)
  self.footer=self.label(self.root,'Офлайн режим • Нәтижелер осы компьютерде сақталады',10,color='#566A88');self.footer.pack(fill='x',pady=3)
 def clear(self):
  for w in self.body.winfo_children():w.destroy()
 def panel(self,parent=None):return tk.Frame(parent or self.body,bg=WHITE,highlightbackground='#C8D9EF',highlightthickness=1,padx=15,pady=13)
 def refresh_score(self):self.scorelabel.config(text=f'⭐ {self.score} ұпай | ❌ {self.mistakes} қате')
 def login(self):
  self.page='login';self.clear();box=self.panel();box.pack(expand=True,fill='x',padx=80,pady=35)
  self.label(box,'Қош келдің, жас зерттеуші!',23,True,BLUE).pack(pady=14)
  self.label(box,'Компьютер құрылғыларын зертте, құрастыр, тапсырмаларды орында.').pack(pady=5)
  self.label(box,'Оқушының аты-жөні',12,True).pack(anchor='w',pady=(17,4))
  tk.Entry(box,textvariable=self.name,font=('Segoe UI',14)).pack(fill='x',pady=4)
  self.label(box,'Сыныбы',12,True).pack(anchor='w',pady=(13,4))
  tk.Entry(box,textvariable=self.class_name,font=('Segoe UI',13)).pack(fill='x',pady=4)
  self.btn(box,'▶ Оқушы ретінде кіру',self.start,True).pack(fill='x',pady=16)
  self.btn(box,'Мұғалім панелін ашу',self.teacher_login).pack(fill='x',pady=5)
  self.label(box,'Назар аудар: нақты компьютер корпусын мұғалімнің рұқсатынсыз ашпа.',10,color=RED).pack(pady=12)
 def start(self):
  name=self.name.get().strip();cls=self.class_name.get().strip()
  if not name or not cls:messagebox.showwarning('Толтыру қажет','Оқушының аты-жөні мен сыныбын енгізіңіз.');return
  self.score=self.mistakes=self.attempts=0;self.explored=set();self.placed=set();self.credited=set();self.quiz_done=set();self.diagnose_done=set();self.selected=None;self.refresh_score();self.mode='student'
  with connect() as c:
   cur=c.execute('INSERT INTO sessions(student,class_name,started) VALUES(?,?,?)',(name,cls,datetime.now().isoformat(timespec='seconds')));self.session=cur.lastrowid
  self.show('explore')
 def nav(self):
  bar=tk.Frame(self.body,bg=WHITE);bar.pack(fill='x',padx=12,pady=(10,3))
  items=[('Зертхана','explore'),('Құрастыру','assemble'),('Ақауды тап','diagnose'),('Тест','quiz'),('Менің нәтижем','results')]
  for title,page in items:self.btn(bar,title,lambda p=page:self.show(p),page==self.page).pack(side='left',padx=3,pady=5)
  self.btn(bar,'Сабақты аяқтау',self.finish).pack(side='right',padx=5,pady=5)
 def show(self,page):
  self.page=page;self.clear();self.nav();getattr(self,'page_'+page)()
 def heading(self,title,subtitle):
  f=tk.Frame(self.body,bg=BG);f.pack(fill='x',padx=18,pady=(8,6));self.label(f,title,21,True,BLUE).pack(anchor='w');self.label(f,subtitle,11,color='#405777',wraplength=1060,justify='left').pack(anchor='w',pady=3)
 def record(self,section,question,answer,ok,points=0):
  self.attempts+=1
  if ok:self.score+=points
  else:self.mistakes+=1
  self.refresh_score()
  with connect() as c:
   c.execute('INSERT INTO events(session_id,time,section,question,answer,correct) VALUES(?,?,?,?,?,?)',(self.session,datetime.now().isoformat(timespec='seconds'),section,question,answer,int(ok)))
   c.execute('UPDATE sessions SET score=?,mistakes=?,attempts=?,explored=?,assembled=?,quiz_correct=?,diagnosis_correct=? WHERE id=?',(self.score,self.mistakes,self.attempts,len(self.explored),len(self.placed),len(self.quiz_done),len(self.diagnose_done),self.session))
 def speak(self,text):
  if not self.sound.get():return
  if sys.platform!='win32':self.footer.config(text='Дыбыстау Windows жүйесінде қолжетімді.');return
  self.speech_token+=1;token=self.speech_token
  def job():
   try:
    escaped=text.replace("'","''")[:600]
    script="Add-Type -AssemblyName System.Speech; $s=New-Object System.Speech.Synthesis.SpeechSynthesizer; $v=@($s.GetInstalledVoices()|Where-Object {$_.Enabled -and $_.VoiceInfo.Culture.Name -eq 'kk-KZ'}); if($v.Count -eq 0){exit 14}; $s.SelectVoice($v[0].VoiceInfo.Name); $s.Rate=-2; $s.Speak('"+escaped+"')"
    encoded=base64.b64encode(script.encode('utf-16le')).decode()
    result=subprocess.run(['powershell','-NoProfile','-NonInteractive','-EncodedCommand',encoded],capture_output=True,timeout=30,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if result.returncode==14:msg='Қазақша дыбыс жоқ: Windows жүйесіне kk-KZ дауысын орнатыңыз.'
    elif result.returncode:msg='Дыбыстау іске қосылмады. Мәтінді экраннан оқуға болады.'
    else:msg='🔊 Анықтама дыбысталды.'
   except Exception:msg='Дыбыстау қолжетімсіз. Мәтінді экраннан оқыңыз.'
   try:self.root.after(0,lambda:self.footer.config(text=msg) if token==self.speech_token else None)
   except Exception:pass
  threading.Thread(target=job,daemon=True).start()
 def toggle_sound(self):
  self.sound.set(not self.sound.get())
  for w in self.header.winfo_children():
   if isinstance(w,tk.Button) and w.cget('text').startswith('🔊 Дыбыс'):w.config(text='🔊 Дыбыс: қосулы' if self.sound.get() else '🔊 Дыбыс: өшірулі')
  self.footer.config(text='Дыбыстау қосылды. Қазақша Windows дауысы қажет.' if self.sound.get() else 'Дыбыстау өшірілді.')
 def page_explore(self):
  self.heading('🔬 Құрылғыларды зерттеу','1. Құрылғыны таңда. 2. Оның қызметін және орналасуын оқы. 3. Құрастыруға өт.')
  shell=self.panel();shell.pack(fill='both',expand=True,padx=12,pady=4)
  left=tk.Frame(shell,bg=WHITE,width=265);left.pack(side='left',fill='y',padx=(0,12));left.pack_propagate(False)
  middle=tk.Frame(shell,bg=WHITE);middle.pack(side='left',fill='both',expand=True)
  right=tk.Frame(shell,bg=WHITE,width=335);right.pack(side='right',fill='y',padx=(12,0));right.pack_propagate(False)
  self.label(left,'5 құрылғыны зертте',14,True,BLUE).pack(anchor='w',pady=(0,8))
  for key,name,_,_ in PARTS:self.btn(left,name,lambda k=key:self.select_part(k)).pack(fill='x',pady=5)
  self.progress=self.label(left,f'Зерттелді: {len(self.explored)}/5',12,True,GREEN);self.progress.pack(anchor='w',pady=12)
  self.btn(left,'Құрастыруға өт →',lambda:self.show('assemble'),True).pack(fill='x',pady=8)
  self.label(middle,'ЖҮЙЕЛІК БЛОКТЫҢ СЫЗБАСЫ',12,True,BLUE).pack(anchor='w')
  self.explore_canvas=tk.Canvas(middle,bg='#EAF2FF',highlightthickness=0,height=460,cursor='hand2')
  self.explore_canvas.pack(fill='both',expand=True,pady=8)
  self.explore_canvas.bind('<Configure>',lambda e:self.draw_case(self.explore_canvas,explore=True))
  self.explore_canvas.bind('<Button-1>',self.explore_click)
  self.info_title=self.label(right,'Құрылғыны таңда',17,True,BLUE,wraplength=320,justify='left');self.info_title.pack(anchor='w',pady=(2,9))
  self.info_text=self.label(right,'Сол жақтағы атауды немесе суреттегі бөлшекті бас.',12,wraplength=310,justify='left');self.info_text.pack(anchor='w',pady=5)
  self.btn(right,'🔊 Анықтаманы тыңдау',lambda:self.speak(P[self.selected][1]+'. '+DETAILS[self.selected][1]+'. '+DETAILS[self.selected][3]) if self.selected else messagebox.showinfo('Таңдау','Алдымен құрылғыны таңдаңыз.'),True).pack(fill='x',pady=10)
  self.select_part('board')
 def select_part(self,key):
  self.selected=key;self.explored.add(key)
  self.info_title.config(text=P[key][1]);d=DETAILS[key]
  self.info_text.config(text=f'{d[0]}\n{d[1]}\n\n{d[2]}\n{d[3]}\n\n{d[4]}\n{d[5]}')
  self.progress.config(text=f'Зерттелді: {len(self.explored)}/5')
  with connect() as c:c.execute('UPDATE sessions SET explored=? WHERE id=?',(len(self.explored),self.session))
  self.draw_case(self.explore_canvas,explore=True)
  self.speak(P[key][1]+'. '+d[1])
 def canvas_xy(self,canvas,event):
  return (event.x*720/max(canvas.winfo_width(),1),event.y*460/max(canvas.winfo_height(),1))
 def target_at(self,x,y):
  # Smaller overlapping parts must be hit before motherboard.
  for k in ['cpu','ram','ssd','psu','board']:
   a,b,c,d=ZONES[k]
   if a<=x<=c and b<=y<=d:return k
  return None
 def explore_click(self,event):
  x,y=self.canvas_xy(self.explore_canvas,event);key=self.target_at(x,y)
  if key:self.select_part(key)
 def draw_case(self,canvas,explore=False):
  canvas.delete('all')
  w=max(canvas.winfo_width(),1);h=max(canvas.winfo_height(),1)
  sx=w/720;sy=h/460
  def rect(x1,y1,x2,y2,**kw):return canvas.create_rectangle(x1*sx,y1*sy,x2*sx,y2*sy,**kw)
  def oval(x1,y1,x2,y2,**kw):return canvas.create_oval(x1*sx,y1*sy,x2*sx,y2*sy,**kw)
  def txt(x,y,text,size=12,**kw):return canvas.create_text(x*sx,y*sy,text=text,font=('Segoe UI',max(8,int(size*min(sx,sy))),'bold'),**kw)
  rect(12,12,710,447,fill='#152944',outline='#557EA8',width=4)
  rect(24,24,695,434,fill='#223B59',outline='#A4C5E8',width=2)
  for x in (655,677):
   for y in (65,95,125,155,185,215,245,275,305,335,365):rect(x,y,x+9,y+12,fill='#46647D',outline='')
  # Motherboard is physically the first item to install.
  board_on=explore or 'board' in self.placed
  rect(145,65,565,390,fill='#116257' if board_on else '#315271',outline='#79D9CA' if board_on else '#8EB1D3',width=3,dash=() if board_on else (6,5))
  if board_on:
   for i in range(4):rect(160+i*16,80,169+i*16,115,fill='#39BBA7',outline='')
   for i in range(5):rect(170+i*62,355,205+i*62,368,fill='#214A3F',outline='#5CC9B5')
  txt(352,96,'АНАЛЫҚ ТАҚША',14,fill='#E4FFF6' if board_on else '#D7E9FF')
  for k in ['cpu','ram','ssd','psu']:
   x1,y1,x2,y2=ZONES[k];on=explore or k in self.placed
   if k=='cpu':color='#E7AC4A';label='CPU\nПроцессор'
   elif k=='ram':color='#9B83F4';label='RAM\nЖедел жад'
   elif k=='ssd':color='#5DBCE7';label='SSD'
   else:color='#DA8399';label='PSU\nҚуат көзі'
   rect(x1,y1,x2,y2,fill=color if on else '#203B57',outline='#FFFFFF' if on else '#9CC4EB',width=2,dash=() if on else (5,4))
   if on:
    if k=='cpu':
     for t in range(4):rect(x1+9+t*18,y1+8,x1+15+t*18,y1+15,fill='#FBE9BA',outline='')
    if k=='ram':
     for t in range(4):rect(x1+10,y1+12+t*32,x2-10,y1+31+t*32,fill='#473C8C',outline='')
    if k=='psu':oval(x1+32,y1+12,x1+96,y1+76,fill='#A94E65',outline='#FBE2EA',width=2)
   txt((x1+x2)/2,(y1+y2)/2,label,12,fill='#112C46' if on else '#E3EFFF',justify='center')
  if not explore and self.selected and self.selected not in self.placed:
   txt(355,418,'Таңдалды: '+P[self.selected][1]+' → орнын бас',11,fill='#FFE09C')
  elif not explore:txt(355,418,'Бөлшекті таңда да, белгіленген орнын бас',11,fill='#FFE09C')
  if explore and self.selected:
   x1,y1,x2,y2=ZONES[self.selected];rect(x1,y1,x2,y2,fill='',outline='#FFF279',width=5)
 def page_assemble(self):
  self.heading('🧩 ЖҮЙЕЛІК БЛОКТЫ ҚҰРАСТЫР','Бөлшекті таңда да, жүйелік блоктағы дұрыс орнына бас. Алдымен аналық тақшаны орналастыр!')
  area=self.panel();area.pack(fill='both',expand=True,padx=12,pady=4)
  left=tk.Frame(area,bg=WHITE,width=270);left.pack(side='left',fill='y',padx=(0,12));left.pack_propagate(False)
  right=tk.Frame(area,bg=WHITE);right.pack(side='left',fill='both',expand=True)
  self.label(left,'1. БӨЛШЕКТІ ТАҢДА',13,True,BLUE).pack(anchor='w',pady=5)
  self.label(left,'Батырманы бас немесе суретке сүйре.',10,color='#4A607C',wraplength=240,justify='left').pack(anchor='w',pady=4)
  self.shelf={}
  for key,name,_,_ in PARTS:
   b=self.btn(left,name,lambda k=key:self.choose_part(k));b.pack(fill='x',pady=6)
   b.bind('<ButtonPress-1>',lambda e,k=key:self.drag_begin(e,k),add='+')
   b.bind('<ButtonRelease-1>',lambda e,k=key:self.drag_end(e,k),add='+')
   self.shelf[key]=b
  self.label(left,'ОРНАТУ РЕТІ',12,True,BLUE).pack(anchor='w',pady=(12,4))
  self.label(left,'1. Аналық тақша\n2. Процессор\n3. Жедел жад\n4. SSD жинақтауыш\n5. Қуат көзі',11,wraplength=245,justify='left').pack(anchor='w')
  self.label(right,'2. БӨЛШЕКТІҢ ОРНЫН БАС',13,True,BLUE).pack(anchor='w',pady=5)
  self.case_canvas=tk.Canvas(right,bg='#EAF2FF',highlightthickness=0,cursor='hand2')
  self.case_canvas.pack(fill='both',expand=True,pady=5)
  self.case_canvas.bind('<Configure>',lambda e:self.draw_case(self.case_canvas))
  self.case_canvas.bind('<Button-1>',self.case_click)
  bottom=tk.Frame(self.body,bg=BG);bottom.pack(fill='x',padx=15,pady=5)
  self.assembly_feedback=self.label(bottom,f'Орнатылған: {len(self.placed)}/5. Аналық тақшаны таңда.',11,True,BLUE,wraplength=650,justify='left');self.assembly_feedback.pack(side='left',fill='x',expand=True)
  self.btn(bottom,'Қайта бастау',self.reset_assembly).pack(side='right',padx=4)
  self.btn(bottom,'Тексеру',self.check_assembly,True).pack(side='right',padx=4)
  for key in self.placed:self.shelf[key].config(text='✓ '+P[key][1],state='disabled',bg='#E3F7EB')
  self.draw_case(self.case_canvas)
 def drag_begin(self,event,key):
  self.drag_key=key
 def drag_end(self,event,key):
  # Drop is detected using screen coordinates, not widget-local coordinates.
  if self.drag_key!=key:return
  self.drag_key=None
  if key in self.placed:return
  x=event.x_root-self.case_canvas.winfo_rootx();y=event.y_root-self.case_canvas.winfo_rooty()
  if 0<=x<self.case_canvas.winfo_width() and 0<=y<self.case_canvas.winfo_height():
   self.selected=key;self.place(self.target_at(x*720/max(self.case_canvas.winfo_width(),1),y*460/max(self.case_canvas.winfo_height(),1)))
 def choose_part(self,key):
  if key in self.placed:return
  self.selected=key
  for k,b in self.shelf.items():
   if k not in self.placed:b.config(bg='#C9E0FF' if k==key else WHITE)
  self.assembly_feedback.config(text=f'Таңдалды: {P[key][1]}. Енді суреттегі дұрыс орнын бас.',fg=BLUE)
  self.draw_case(self.case_canvas)
 def case_click(self,event):
  x,y=self.canvas_xy(self.case_canvas,event);self.place(self.target_at(x,y))
 def place(self,slot):
  if not self.selected or self.selected in self.placed:
   self.assembly_feedback.config(text='Алдымен сол жақтан бөлшекті таңда!',fg=RED);return
  key=self.selected
  if slot is None:
   self.assembly_feedback.config(text='Жүйелік блоктағы белгіленген ұяшықты бас.',fg=RED);return
  if slot in self.placed:
   self.assembly_feedback.config(text='Бұл орын толтырылған. Басқа орынды таңда.',fg=RED);return
  ok=key==slot and (key=='board' or 'board' in self.placed)
  self.record('Құрастыру',P[slot][1],P[key][1],ok,20 if key not in self.credited else 0)
  if ok:
   self.placed.add(key);new_points=key not in self.credited;self.credited.add(key);self.shelf[key].config(text='✓ '+P[key][1],state='disabled',bg='#E3F7EB');self.selected=None
   self.assembly_feedback.config(text=f'Дұрыс! {P[key][1]} орнатылды. '+('+20 ұпай. ' if new_points else 'Ұпай бұрын есептелген. ')+f'Барлығы: {len(self.placed)}/5',fg=GREEN)
   if len(self.placed)==5:self.assembly_feedback.config(text='Тамаша! Компьютердің барлық 5 бөлшегі орнатылды. «Тексеру» батырмасын бас.',fg=GREEN)
  else:
   hint='Алдымен аналық тақшаны орнат.' if key!='board' and 'board' not in self.placed else 'Бөлшектің атауын және ұяшығын салыстыр.'
   self.assembly_feedback.config(text=f'Қате! {hint} Қате саны +1.',fg=RED)
  self.draw_case(self.case_canvas)
 def reset_assembly(self):
  if messagebox.askyesno('Қайта бастау','Бөлшектерді қайтадан жинайсыз ба? (Алынған ұпайлар мен қателер сақталады.)'):
   self.placed=set();self.selected=None
   with connect() as c:c.execute('UPDATE sessions SET assembled=0 WHERE id=?',(self.session,))
   self.show('assemble')
 def check_assembly(self):
  if len(self.placed)==5:messagebox.showinfo('Дұрыс!','Компьютер дұрыс құрастырылды! 5/5. Келесі бөлімге өт.');self.show('diagnose')
  else:messagebox.showinfo('Әлі аяқталмады',f'{len(self.placed)}/5 орнатылды. Қалған {5-len(self.placed)} құрылғыны орнына қой.')
 def page_diagnose(self):self.question_page('diagnose')
 def page_quiz(self):self.question_page('quiz')
 def question_page(self,kind):
  done=self.diagnose_done if kind=='diagnose' else self.quiz_done
  title='🩺 Ақауды анықта' if kind=='diagnose' else '☑ Білімді тексеру'
  self.heading(title,'Жауапты таңда. Әр дұрыс жауапқа 20 ұпай беріледі, қателер есептеледі.')
  idx=next((i for i in range(5) if i not in done),None)
  box=self.panel();box.pack(fill='both',expand=True,padx=18,pady=8)
  if idx is None:
   self.label(box,'Барлық 5 тапсырма орындалды!',21,True,GREEN).pack(pady=25)
   self.btn(box,'Нәтижені көру',lambda:self.show('results'),True).pack(pady=15)
   return
  self.label(box,f'{len(done)+1}/5 тапсырма',13,True,BLUE).pack(anchor='w',pady=8)
  if kind=='diagnose':key=PARTS[idx][0];question=PARTS[idx][3]+' Қай құрылғы қажет?'
  else:question,key=QUESTIONS[idx]
  self.label(box,question,17,True,wraplength=850,justify='left').pack(anchor='w',pady=20)
  opts=list(P.keys());random.Random(idx+(11 if kind=='diagnose' else 19)).shuffle(opts)
  for option in opts:self.btn(box,P[option][1],lambda o=option,k=key,q=question,i=idx:self.answer(kind,i,q,k,o)).pack(fill='x',pady=5)
 def answer(self,kind,idx,question,key,option):
  done=self.diagnose_done if kind=='diagnose' else self.quiz_done
  if idx in done:return
  ok=key==option;done.add(idx);self.record('Ақауды тап' if kind=='diagnose' else 'Тест',question,P[option][1],ok,20)
  msg=('Дұрыс! +20 ұпай. ' if ok else 'Қате. Дұрыс жауап: '+P[key][1]+'. ')+P[key][2]
  messagebox.showinfo('NEURO кеңесшісі',msg);self.speak(msg);self.show(kind)
 def page_results(self):
  self.heading('🏆 Менің нәтижем','Барлық қателер мен ұпайлар автоматты түрде сақталады.')
  box=self.panel();box.pack(fill='both',expand=True,padx=18,pady=7)
  for line in [f'Оқушы: {self.name.get()} | {self.class_name.get()}',f'Жиналған ұпай: {self.score}',f'Қателер саны: {self.mistakes}',f'Барлық жауап әрекеті: {self.attempts}',f'Зерттелген құрылғылар: {len(self.explored)}/5',f'Құрастырылған құрылғылар: {len(self.placed)}/5',f'Ақау тапсырмалары: {len(self.diagnose_done)}/5',f'Тест тапсырмалары: {len(self.quiz_done)}/5']:
   self.label(box,line,14,True if 'ұпай' in line or 'Қателер' in line else False).pack(anchor='w',pady=6)
  self.btn(box,'Сабақты аяқтау және нәтижені сақтау',self.finish,True).pack(anchor='w',pady=15)
 def finish(self):
  if self.session:
   with connect() as c:c.execute('UPDATE sessions SET finished=?,status=?,score=?,mistakes=?,attempts=?,explored=?,assembled=?,quiz_correct=?,diagnosis_correct=? WHERE id=?',(datetime.now().isoformat(timespec='seconds'),'Аяқталды',self.score,self.mistakes,self.attempts,len(self.explored),len(self.placed),len(self.quiz_done),len(self.diagnose_done),self.session))
  messagebox.showinfo('Сабақ аяқталды',f'{self.name.get()}\nҰпай: {self.score}\nҚате: {self.mistakes}\nНәтиже сақталды.');self.session=None;self.login()
 def teacher_login(self):
  # Local teacher view is not a security boundary; PIN can be configured via environment variable.
  from tkinter import simpledialog
  pin=simpledialog.askstring('Мұғалім панелі','Мұғалім PIN кодын енгізіңіз:',show='*',parent=self.root)
  if pin is None:return
  if pin!=os.environ.get('NEUROCHIP_TEACHER_PIN','1234'):messagebox.showerror('Қате','PIN код дұрыс емес.');return
  self.mode='teacher';self.teacher()
 def teacher(self):
  self.clear();self.page='teacher'
  top=tk.Frame(self.body,bg=BG);top.pack(fill='x',padx=15,pady=10)
  self.label(top,'📊 Мұғалім панелі — оқушылардың нәтижелері',19,True,BLUE).pack(side='left')
  self.btn(top,'Шығу',self.login).pack(side='right',padx=5)
  self.btn(top,'CSV экспорт',self.export_csv,True).pack(side='right',padx=5)
  self.btn(top,'Жаңарту',self.teacher).pack(side='right',padx=5)
  with connect() as c:rows=c.execute('SELECT id,student,class_name,started,score,mistakes,attempts,explored,assembled,quiz_correct,diagnosis_correct,status FROM sessions ORDER BY id DESC').fetchall()
  summary=self.panel();summary.pack(fill='x',padx=15,pady=5)
  self.label(summary,f'Оқушы сессиялары: {len(rows)}    Жалпы ұпай: {sum(r[4] for r in rows)}    Жалпы қате: {sum(r[5] for r in rows)}',13,True).pack(anchor='w')
  frame=self.panel();frame.pack(fill='both',expand=True,padx=15,pady=5)
  cols=('id','student','class','date','score','mistakes','attempts','explored','assembled','quiz','diagnose','status')
  headings=('№','Оқушы','Сынып','Күні','Ұпай','Қате','Әрекет','Зерттеу','Құрастыру','Тест','Ақау','Күйі')
  tree=ttk.Treeview(frame,columns=cols,show='headings',height=13)
  for col,head in zip(cols,headings):tree.heading(col,text=head);tree.column(col,width=90 if col not in ('student','date') else 145,anchor='center')
  for row in rows:tree.insert('', 'end',values=row)
  ys=ttk.Scrollbar(frame,orient='vertical',command=tree.yview);xs=ttk.Scrollbar(frame,orient='horizontal',command=tree.xview);tree.configure(yscrollcommand=ys.set,xscrollcommand=xs.set)
  tree.grid(row=0,column=0,sticky='nsew');ys.grid(row=0,column=1,sticky='ns');xs.grid(row=1,column=0,sticky='ew');frame.grid_columnconfigure(0,weight=1);frame.grid_rowconfigure(0,weight=1)
  self.teacher_tree=tree
  self.btn(self.body,'Таңдалған оқушының қателері мен жауаптарын көру',self.details,True).pack(pady=8)
 def details(self):
  selection=self.teacher_tree.selection()
  if not selection:messagebox.showinfo('Таңдау','Кестеден оқушыны таңдаңыз.');return
  session_id=int(self.teacher_tree.item(selection[0],'values')[0]);win=tk.Toplevel(self.root);win.title('Оқушының жауаптары');win.geometry('800x520')
  text=tk.Text(win,font=('Segoe UI',11),wrap='word');text.pack(fill='both',expand=True,padx=10,pady=10)
  with connect() as c:
   rows=c.execute('SELECT time,section,question,answer,correct FROM events WHERE session_id=? ORDER BY id',(session_id,)).fetchall()
  for dt,section,question,answer,ok in rows:text.insert('end',f'{dt} | {section} | {"ДҰРЫС" if ok else "ҚАТЕ"}\nСұрақ: {question}\nЖауап: {answer}\n\n')
  if not rows:text.insert('end','Әзірше жауап әрекеттері жоқ.')
  text.config(state='disabled')
 def export_csv(self):
  path=filedialog.asksaveasfilename(title='Нәтижелерді сақтау',defaultextension='.csv',filetypes=[('CSV файл','*.csv')])
  if not path:return
  with connect() as c:rows=c.execute('SELECT student,class_name,started,finished,score,mistakes,attempts,explored,assembled,quiz_correct,diagnosis_correct,status FROM sessions ORDER BY id').fetchall()
  try:
   with open(path,'w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f,delimiter=';');w.writerow(['Оқушы','Сынып','Басталған уақыты','Аяқталған уақыты','Ұпай','Қате','Әрекет','Зерттеу','Құрастыру','Тест','Ақау','Күйі']);w.writerows(rows)
   messagebox.showinfo('Сақталды','CSV файлы сақталды.')
  except OSError as e:messagebox.showerror('Қате',str(e))

if __name__=='__main__':
 root=tk.Tk();App(root);root.mainloop()
