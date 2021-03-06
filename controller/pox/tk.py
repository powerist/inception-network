# Copyright 2012 James McCauley
#
# This file is part of POX.
#
# POX is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# POX is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with POX.  If not, see <http://www.gnu.org/licenses/>.

"""
Lets you use Tk with POX.

Highly experimental.
"""

from collections import deque
from pox.core import core

log = core.getLogger()

#TODO: Bind revent events across thread

class MessageBoxer (object):
  def __init__ (self, tk):
    import tkMessageBox, tkColorChooser, tkSimpleDialog, tkFileDialog
    fields = "ERROR INFO QUESTION WARNING ABORTRETRYIGNORE OKCANCEL "
    fields += "RETRYCANCEL YESNO YESNOCANCEL ABORT RETRY IGNORE OK "
    fields += "CANCEL YES NO"
    for f in fields.split():
      setattr(self, f, getattr(tkMessageBox, f))

    methods = "showinfo showwarning showerror askquestion "
    methods += "askokcancel askyesno askretrycancel"
    self._addmethods(tkMessageBox, methods, tk)

    methods = "askinteger askfloat askstring"
    self._addmethods(tkSimpleDialog, methods, tk)

    methods = "askcolor"
    self._addmethods(tkColorChooser, methods, tk)

    methods = "askopenfilename asksaveasfilename"
    self._addmethods(tkFileDialog, methods, tk)

  def _addmethods (self, module, methods, tk):
    for m in methods.split():
      def f (m):
        def f2 (*args, **kw):
          return getattr(module, m)(*args,**kw)
        def f4 (*args, **kw):
          _ = kw.pop('_', None)
          tk.do_ex(getattr(module, m), rv = _, args=args, kw=kw)
        def f5 (_, *args, **kw):
          tk.do_ex(f2, rv = _, args=args, kw=kw)
        return f4,f5
      a,b = f(m)
      setattr(self, m, a)
      setattr(self, m+"_cb", b)

 
class Tk (object):
  _core_name = "tk"

  def __init__ (self):
    self._q = deque()
    self.dialog = MessageBoxer(self)
    self.root = None
    self.automatic_quit = True

  def do_ex (self, code, rv=None, args=[], kw={}):
    self._q.append((code, rv, args, kw))
    self._ping()

  def _ping (self):
    if not self.root: return
    self.root.event_generate('<<Ping>>', when='tail')

  def do (__self, __code, __rv=None, *args, **kw):
    __self._q.append((__code, __rv, args, kw))
    __self._ping()
    
  def _dispatch (self, event):
    while len(self._q):
      self._dispatch_one(*self._q.popleft())

  def _dispatch_one (self, code, rv, args, kw):
    if callable(code):
      r = code(*args, **kw)
    else:
      def f ():
        l = {'self':self}
        l.update(kw)
        exec code in globals(), l
      r = f()
    if rv: core.callLater(rv, r)

  def run (self):
    import Tkinter
    root = Tkinter.Tk()
    root.bind('<<Ping>>', self._dispatch)

    self.root = root

    # Become live once in a while so that signals get handled
    def timer ():
      if self.automatic_quit and core.running == False:
        root.quit()
        return
      root.after(500, timer)
    timer()

    self.root.withdraw()

    self._dispatch(None)

    try:
      root.mainloop()
    except KeyboardInterrupt:
      pass
    log.debug("Quitting")


def launch ():
  import boot
  core.registerNew(Tk)
  boot.set_main_function(core.tk.run)

  """
  def pr (msg):
    print "From Tk:", msg
  core.callDelayed(5,lambda: core.tk.msgbox.showinfo_cb(pr,
      "Hello", "Hello, World!"))
  """
