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

def connect():
 c=sqlite3.connect(DB)
 c.execute('CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY, student TEXT NOT NULL, class_name TEXT NOT NULL, started TEXT NOT NULL, finished TEXT, score INTEGER DEFAULT 0, mistakes INTEGER DEFAULT 0, attempts INTEGER DEFAULT 0, explored INTEGER DEFAULT 0, assembled INTEGER DEFAULT 0, quiz_correct INTEGER DEFAULT 0, diagnosis_correct INTEGER DEFAULT 0, status TEXT DEFAULT "Орындалуда")')
 c.execute('CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, session_id INTEGER, time TEXT, section TEXT, question TEXT, answer TEXT, correct INTEGER, FOREIGN KEY(session_id) REFERENCES sessions(id))')
 c.commit();return c

class App:
 def __init__(self,root):
  self.root=root;root.title('NEURO•CHIP LAB 3 — Оқушы зертханасы және мұғалім панелі');root.geometry('1220x800');root.minsize(940,630);root.configure(bg=BG)
  self.name=tk.StringVar();self.class_name=tk.StringVar(value='3-сынып');self.sound=tk.BooleanVar(value=False)
  self.session=None;self.score=0;self.mistakes=0;self.attempts=0;self.explored=set();self.placed=set();self.quiz_done=set();self.diagnose_done=set();self.selected=None;self.mode='student';self.page='login';self.photo=None;self.speech_token=0
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
  self.score=self.mistakes=self.attempts=0;self.explored=set();self.placed=set();self.quiz_done=set();self.diagnose_done=set();self.selected=None;self.refresh_score();self.mode='student'
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
  self.heading('🔬 Құрылғыларды зерттеу','Құрылғының атауын бас. Оң жақтан анықтамасын оқы. «Тыңдау» батырмасын басып тыңда.')
  shell=self.panel();shell.pack(fill='both',expand=True,padx=15,pady=6)
  left=tk.Frame(shell,bg=WHITE);left.pack(side='left',fill='both',expand=True)
  right=tk.Frame(shell,bg=WHITE,width=350);right.pack(side='right',fill='y',padx=(15,0));right.pack_propagate(False)
  self.label(left,'Құрылғыны таңда:',14,True).pack(anchor='w',pady=7)
  for key,name,description,_ in PARTS:self.btn(left,name,lambda k=key:self.select_part(k)).pack(fill='x',pady=5)
  self.label(left,'Әр құрылғыны таңдаған сайын оның қызметін білесің.',11,color='#536783',wraplength=460,justify='left').pack(anchor='w',pady=14)
  self.info_title=self.label(right,'Бөлшекті таңда',17,True,BLUE,wraplength=320,justify='left');self.info_title.pack(anchor='w',pady=10)
  self.info_text=self.label(right,'Сол жақтағы бес құрылғының біреуін бас.',13,wraplength=315,justify='left');self.info_text.pack(anchor='w',pady=13)
  self.btn(right,'🔊 Анықтаманы тыңдау',lambda:self.speak(P[self.selected][1]+'. '+P[self.selected][2]) if self.selected else messagebox.showinfo('Таңдау','Алдымен құрылғыны таңдаңыз.'),True).pack(fill='x',pady=10)
  self.progress=self.label(right,f'Зерттелген құрылғылар: {len(self.explored)}/5',12,True,GREEN);self.progress.pack(anchor='w',pady=10)
  self.btn(right,'Келесі: құрастыру →',lambda:self.show('assemble'),True).pack(fill='x',pady=12)
 def select_part(self,key):
  self.selected=key;self.explored.add(key);self.info_title.config(text=P[key][1]);self.info_text.config(text=P[key][2]);self.progress.config(text=f'Зерттелген құрылғылар: {len(self.explored)}/5')
  with connect() as c:c.execute('UPDATE sessions SET explored=? WHERE id=?',(len(self.explored),self.session))
  self.speak(P[key][1]+'. '+P[key][2])
 def page_assemble(self):
  self.heading('🧩 Компьютерді құрастыру','1. Сол жақтан бөлшекті бас. 2. Оң жақтан дәл сондай ұяшықты бас. 3. Қате таңдасаң, қайта көр.')
  area=self.panel();area.pack(fill='both',expand=True,padx=15,pady=6)
  left=tk.Frame(area,bg=WHITE);left.pack(side='left',fill='both',expand=True,padx=(0,15))
  right=tk.Frame(area,bg=WHITE);right.pack(side='right',fill='both',expand=True)
  self.label(left,'1. БӨЛШЕКТЕР СӨРЕСІ',15,True,BLUE).pack(anchor='w',pady=6)
  self.shelf={}
  for key,name,_,_ in PARTS:
   b=self.btn(left,name,lambda k=key:self.choose_part(k));b.pack(fill='x',pady=6);self.shelf[key]=b
  self.label(right,'2. ЖҮЙЕЛІК БЛОК ҰЯШЫҚТАРЫ',15,True,BLUE).pack(anchor='w',pady=6)
  self.slots={}
  for key,name,_,_ in PARTS:
   b=self.btn(right,'□ '+name,lambda k=key:self.place(k));b.pack(fill='x',pady=6);self.slots[key]=b
  bottom=tk.Frame(self.body,bg=BG);bottom.pack(fill='x',padx=20,pady=8)
  self.assembly_feedback=self.label(bottom,f'Орнатылған: {len(self.placed)}/5. Бөлшекті таңда.',12,True,BLUE,wraplength=720,justify='left');self.assembly_feedback.pack(side='left',fill='x',expand=True)
  self.btn(bottom,'Қайта бастау',self.reset_assembly).pack(side='right',padx=4)
  self.btn(bottom,'Тексеру',self.check_assembly,True).pack(side='right',padx=4)
  for key in self.placed:self.shelf[key].config(text='✓ '+P[key][1],state='disabled',bg='#E3F7EB');self.slots[key].config(text='✓ '+P[key][1],state='disabled',bg='#E3F7EB')
 def choose_part(self,key):
  if key in self.placed:return
  self.selected=key
  for k,b in self.shelf.items():
   if k not in self.placed:b.config(bg='#C9E0FF' if k==key else WHITE)
  self.assembly_feedback.config(text=f'Таңдалды: {P[key][1]}. Енді оң жақтағы сәйкес ұяшықты бас.',fg=BLUE)
 def place(self,slot):
  if slot in self.placed:return
  if not self.selected or self.selected in self.placed:self.assembly_feedback.config(text='Алдымен сол жақтағы бөлшекті таңда!',fg=RED);return
  key=self.selected;ok=key==slot;self.record('Құрастыру',P[slot][1],P[key][1],ok,20)
  if ok:
   self.placed.add(key);self.shelf[key].config(text='✓ '+P[key][1],state='disabled',bg='#E3F7EB');self.slots[key].config(text='✓ '+P[key][1],state='disabled',bg='#E3F7EB');self.selected=None
   self.assembly_feedback.config(text=f'Дұрыс! +20 ұпай. Орнатылған: {len(self.placed)}/5',fg=GREEN)
   if len(self.placed)==5:self.assembly_feedback.config(text='Тамаша! Бес құрылғы орнатылды. «Тексеру» батырмасын бас.',fg=GREEN)
  else:self.assembly_feedback.config(text=f'Қате! {P[key][1]} құрылғысын өз ұяшығына орналастыр. Қате саны +1.',fg=RED)
 def reset_assembly(self):
  if messagebox.askyesno('Қайта бастау','Орнатылған бөлшектерді қайтадан жинайсыз ба? (Алынған ұпайлар сақталады.)'):
   self.placed=set();self.selected=None
   with connect() as c:c.execute('UPDATE sessions SET assembled=0 WHERE id=?',(self.session,))
   self.show('assemble')
 def check_assembly(self):
  if len(self.placed)==5:messagebox.showinfo('Дұрыс!','Компьютер дұрыс құрастырылды! 5/5. Келесі бөлімге өтіңіз.');self.show('diagnose')
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
