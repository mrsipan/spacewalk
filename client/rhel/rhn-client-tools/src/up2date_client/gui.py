#
# GUI for Update Agent
# Copyright (c) 1999--2016 Red Hat, Inc.  Distributed under GPLv2.
#
# Authors:
#    Preston Brown <pbrown@redhat.com>
#    Adrian Likins <alikins@redhat.com>
#    Daniel Benamy <dbenamy@redhat.com>

import os
import sys

import gtk
import gtk.glade

gtk.glade.bindtextdomain("rhn-client-tools", "/usr/share/locale")

import signal

try: # python2
    import xmlrpclib
except ImportError: # python3
    import xmlrpc.client as xmlrpclib

import gettext
t = gettext.translation('rhn-client-tools', fallback=True)
# Python 3 translations don't have a ugettext method
if not hasattr(t, 'ugettext'):
    t.ugettext = t.gettext
_ = t.ugettext

from up2date_client import up2dateErrors
from up2date_client import config
from up2date_client import rhnreg
from up2date_client import messageWindow

from up2date_client import rhnregGui



class Gui(rhnregGui.StartPage, rhnregGui.ChooseServerPage, rhnregGui.LoginPage,
                rhnregGui.ReviewSubscriptionPage, rhnregGui.CreateProfilePage,
                rhnregGui.ProvideCertificatePage, rhnregGui.FinishPage,
                rhnregGui.ChooseChannelPage):

    def __init__(self):
        self.cfg = config.initUp2dateConfig()

        gladeFile = "/usr/share/rhn/up2date_client/gui.glade"
        self.xml = gtk.glade.XML(gladeFile, "mainWin", domain="rhn-client-tools")
        self.xml.signal_autoconnect (
            { "onMainWinCancel" : self.onMainWinCancel,
              "onMainWinPrepare" : self.onMainWinPrepare,
              "onMainWinApply" : self.onMainWinApply,
        } )

        rhnregGui.StartPage.__init__(self)
        rhnregGui.ChooseServerPage.__init__(self)
        rhnregGui.LoginPage.__init__(self)
        rhnregGui.ChooseChannelPage.__init__(self)
        rhnregGui.CreateProfilePage.__init__(self)
        rhnregGui.ReviewSubscriptionPage.__init__(self)
        rhnregGui.ProvideCertificatePage.__init__(self)
        rhnregGui.FinishPage.__init__(self)

        # Pack all the pages into the empty druid screens
        contents = self.startPageVbox()
        container = self.xml.get_widget("startPageVbox")
        container.pack_start(contents, True)
        contents = self.chooseServerPageVbox()
        container = self.xml.get_widget("chooseServerPageVbox")
        container.pack_start(contents, True)
        contents = self.loginPageVbox()
        container = self.xml.get_widget("loginPageVbox")
        container.pack_start(contents, True)
        contents = self.chooseChannelPageVbox()
        container = self.xml.get_widget("chooseChannelPageVbox")
        container.pack_start(contents, True)
        self.chooseChannelPageVbox = container
        contents = self.createProfilePageVbox()
        container = self.xml.get_widget("createProfilePageVbox")
        container.pack_start(contents, True)
        contents = self.reviewSubscriptionPageVbox()
        container = self.xml.get_widget("reviewSubscriptionPageVbox")
        container.pack_start(contents, True)
        contents = self.provideCertificatePageVbox()
        container = self.xml.get_widget("provideCertificatePageVbox")
        container.pack_start(contents, True)
        self.provideCertificatePageVbox = container
        contents = self.finishPageVbox()
        container = self.xml.get_widget("finishPageVbox")
        container.pack_start(contents, True)

        self.initProfile = False
        self.oemInfo = {}
        self.productInfo = {}
        self.already_registered_already_shown = False
        self.rhsm_already_registered_already_shown = False

#        self.druid = self.xml.get_widget("druid")
        self.mainWin = self.xml.get_widget("mainWin")
        self.mainWin.connect("delete-event", gtk.main_quit)
        self.mainWin.connect("hide", gtk.main_quit)
        self.mainWin.connect("close", gtk.main_quit)

#        # It's better to get widgets in advance so bugs don't hide in get_widget
#        # calls that only get executed periodically.
#        self.startPage = self.xml.get_widget("startPage")
#        self.chooseServerPage = self.xml.get_widget("chooseServerPage")
#        self.provideCertificatePage = self.xml.get_widget("provideCertificatePage")
#        self.loginPage = self.xml.get_widget("loginPage")
#        self.chooseChannelPage = self.xml.get_widget("chooseChannelPage")
#        self.createProfilePage = self.xml.get_widget("createProfilePage")
#        self.reviewSubscriptionPage = \
#            self.xml.get_widget("reviewSubscriptionPage")
#        self.finishPage = self.xml.get_widget("finishPage")
        self.pages = {page.name: n  for n, page in enumerate(self.mainWin.get_children())}

        # Set up cursor changing functions. Overriding functions that aren't in
        # classes like this could be called a hack, but I think it's the best
        # we can do with the current overall setup and isn't too bad.
        def mySetBusyCursor():
            cursor = gtk.gdk.Cursor(gtk.gdk.WATCH)
            self.mainWin.window.set_cursor(cursor)
            while gtk.events_pending():
                gtk.main_iteration(False)
        def mySetArrowCursor():
            cursor = gtk.gdk.Cursor(gtk.gdk.LEFT_PTR)
            self.mainWin.window.set_cursor(cursor)
            while gtk.events_pending():
                gtk.main_iteration(False)
        rhnregGui.setBusyCursor = mySetBusyCursor
        rhnregGui.setArrowCursor = mySetArrowCursor

        self.mainWin.show_all()
        # Druid doesn't signal prepare to the first page when starting up
        self.onStartPagePrepare(None, None, manualPrepare=True)


    def onMainWinCancel(self, mainWin):
        dialog = rhnregGui.ConfirmQuitDialog()
        if dialog.rc == 1:
            self.mainWin.set_current_page(self.pages['finishPageVbox'])
        else:
            return True

    def fatalError(self, error, wrap=1):
        rhnregGui.setArrowCursor()
        # FIXME
        if wrap:
            text = messageWindow.wrap_text(error)
        else:
            text = error

        dlg = messageWindow.ErrorDialog(text,self.mainWin)
        gtk.main_quit()
        sys.exit(1)

    def nextPage(self, vbox):
        # go one page before desired one and 'forward' will move us where we want
        self.mainWin.set_current_page(self.pages[vbox]-1)

    def onMainWinPrepare(self, mainWin, vbox):
        prepare_func = {
              "startPageVbox": self.onStartPagePrepare,
              "chooseServerPageVbox" : self.onChooseServerPagePrepare,
              "loginPageVbox" : self.onLoginPagePrepare,
              "chooseChannelPageVbox" : self.onChooseChannelPagePrepare,
              "createProfilePageVbox" : self.onCreateProfilePagePrepare,
              "reviewSubscriptionPageVbox" : self.onReviewSubscriptionPagePrepare,
              "finishPageVbox" : self.onFinishPagePrepare,
        }
        if vbox.name in prepare_func:
            prepare_func[vbox.name](mainWin, vbox)

    def onMainWinApply(self, mainWin):
       forward_func = {
              "chooseServerPageVbox" : self.onChooseServerPageNext,
              "loginPageVbox" : self.onLoginPageNext,
              "chooseChannelPageVbox" : self.onChooseChannelPageNext,
              "createProfilePageVbox" : self.onCreateProfilePageNext,
              "provideCertificatePageVbox" : self.onProvideCertificatePageNext,
       }
       currentVbox = mainWin.get_nth_page(mainWin.get_current_page())
       if currentVbox.name in forward_func:
           forward_func[currentVbox.name](mainWin, None)

    def onStartPagePrepare(self, mainWin, vbox, manualPrepare=False):
        if rhnreg.rhsm_registered() and not self.rhsm_already_registered_already_shown:
            # Dialog constructor returns when dialog closes
            dialog = rhnregGui.AlreadyRegisteredSubscriptionManagerDialog()
            if dialog.rc == 0:
                sys.exit(0)
            self.rhsm_already_registered_already_shown = True
        if rhnreg.registered() and not self.already_registered_already_shown:
            # Dialog constructor returns when dialog closes
            dialog = rhnregGui.AlreadyRegisteredDialog()
            if dialog.rc == 0:
                sys.exit(0)
            self.already_registered_already_shown = True

    def onChooseServerPagePrepare(self, mainWin, vbox):
        self.chooseServerPagePrepare()

    def onChooseServerPageNext(self, page, dummy):
        try:
            ret = self.chooseServerPageApply()
            if ret: # something went wrong
                self.nextPage('chooseServerPageVbox')
                return
            self.provideCertificatePageVbox.set_visible(False)
            self.nextPage('loginPageVbox')
        except (up2dateErrors.SSLCertificateVerifyFailedError,\
                up2dateErrors.SSLCertificateFileNotFound):
            self.setUrlInWidget()

    def onLoginPagePrepare(self, mainWin, vbox):
        self.loginXml.get_widget("loginUserEntry").grab_focus()
        self.loginPagePrepare()

    def onLoginPageNext(self, page, dummy):
        """This must manually switch pages because another function calls it to
        advance the druid. It returns True to inform the druid of this.
        """
        ret = self.loginPageVerify()
        if ret:
            self.nextPage('loginPageVbox')
            return

        ret = self.loginPageApply()
        if ret:
            self.nextPage('loginPageVbox')
            return

        self.goToPageAfterLogin()


    def goToPageAfterLogin(self):
        """This function is used by the create new account dialog so it doesn't
        need to have any knowledge of the screen mechanism or order.
        """
        if not rhnregGui.ChooseChannelPage.chooseChannelShouldBeShown(self):
            self.chooseChannelPageVbox.set_visible(False)

    def onChooseChannelPageNext(self, page, dummy):
        self.chooseChannelPageApply()
        if self.chose_all_updates or \
           self.chose_default_channel is False:
            dialog = rhnregGui.ConfirmAllUpdatesDialog()
            if dialog.rc == 0:
                self.nextPage('chooseChannelPageVbox')

    def onChooseChannelPagePrepare(self, mainWin, vbox):
        self.chooseChannelPagePrepare()

    def onCreateProfilePagePrepare(self, mainWin, vbox):
        self.createProfilePagePrepare()

    def onCreateProfilePageNext(self, page, dummy):
        ret = self.createProfilePageVerify()
        if ret:
            return ret
        ret = self.createProfilePageApply()
        if ret:
            return ret

    def onReviewSubscriptionPagePrepare(self, mainWin, vbox):
        self.reviewSubscriptionPagePrepare()

    def onProvideCertificatePageNext(self, page=None, dummy=None):
        status = self.provideCertificatePageApply()
        if status == 0:
            pass
        elif status == 1:
            self.nextPage('finishPageVbox')
        elif status == 3:
            self.nextPage('chooseServerPageVbox')
        else:
            assert status == 2
            self.nextPage('provideCertificatePageVbox')
        return


    def onFinishPagePrepare(self, mainWin, vbox):
        if rhnregGui.hasBaseChannelAndUpdates():
#            self.druid.finish.set_label(_("_Finish"))
            title = _("Updates Configured")
        else:
#            self.druid.finish.set_label(_("_Exit"))
            title = _("Software Updates Not Set Up")
        self.finishPagePrepare()
        self.mainWin.set_title(title)
        self.mainWin.set_page_title(vbox, title)


def rootWarning():
    dlg = messageWindow.ErrorDialog(_("You must run rhn_register as root."))
#    dlg.run_and_close()

def errorWindow(msg):
    dlg = messageWindow.ErrorDialog(messageWindow.wrap_text(msg))
#    dlg.run_and_close()

def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    if os.geteuid() != 0:
        rootWarning()
        sys.exit(1)

    gui = Gui()
    gtk.main()


if __name__ == "__main__":
    try:
        main()
    except xmlrpclib.ResponseError:
        print(sys.exc_info()[1])
    except IOError:
        e = sys.exc_info()[1]
        print(_("There was some sort of I/O error: %s") % e.errmsg)
