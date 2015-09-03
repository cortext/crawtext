from jinja2 import Template
from jinja2 import Environment, PackageLoader
from jinja2 import FileSystemLoader
from premailer import transform
import smtplib
from private import username, passw

def createhtmlmail(html, text, subject, fromEmail):
    """Create a mime-message that will render HTML in popular
    MUAs, text in better ones"""
    import MimeWriter
    import mimetools
    import cStringIO
    out = cStringIO.StringIO() # output buffer for our message
    htmlin = cStringIO.StringIO(html)
    txtin = cStringIO.StringIO(text)
    writer = MimeWriter.MimeWriter(out)
    #
    # set up some basic headers... we put subject here
    # because smtplib.sendmail expects it to be in the
    # message body
    #
    writer.addheader("From", fromEmail)
    writer.addheader("Subject", subject)
    writer.addheader("MIME-Version", "1.0")
    #
    # start the multipart section of the message
    # multipart/alternative seems to work better
    # on some MUAs than multipart/mixed
    #
    writer.startmultipartbody("alternative")
    writer.flushheaders()
    #
    # the plain text section
    #
    subpart = writer.nextpart()
    subpart.addheader("Content-Transfer-Encoding", "quoted-printable")
    pout = subpart.startbody("text/plain", [("charset", 'us-ascii')])
    mimetools.encode(txtin, pout, 'quoted-printable')
    txtin.close()
    #
    # start the html subpart of the message
    #
    subpart = writer.nextpart()
    subpart.addheader("Content-Transfer-Encoding", "quoted-printable")
    #
    # returns us a file-ish object we can write to
    #
    pout = subpart.startbody("text/html", [("charset", 'us-ascii')])
    mimetools.encode(htmlin, pout, 'quoted-printable')
    htmlin.close()
    #
    # Now that we're done, close our writer and
    # return the message body
    #
    writer.lastpart()
    msg = out.getvalue()
    out.close()
    return msg

    
def mail_it(title, msg, user, fromaddrs ="crawlbot@playlab.paris"):
    msg = createhtmlmail(html, txt, title, fromaddrs)
    # The actual mail send
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(username,passw)
    if type(user) == list:
        for u in user: 
            server.sendmail(fromaddrs, u, msg)
    else:
        server.sendmail(fromaddrs, user, msg)
    server.quit()
    return True

def send_mail(user, template_name, values, txt):
    fromaddrs = "crawlbot@playlab.paris"
    #env = Environment(loader=FileSystemLoader('./'))
    env = Environment(loader=PackageLoader('packages', 'templates'))
    tpl = "./"+template_name
    template = env.get_template(tpl)
    html = template.render(stats=values)
    html = transform(html)
    if template_name == "crawl.html":
        title = "CrawText | %s | Crawl StatS" %values["project_name"]
    
    else:
        title = "CrawText | %s |%s Report" %(values["project_name"], template_name)
        
    msg = createhtmlmail(html, txt, title, fromaddrs)
    # The actual mail send
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(username,passw)
    if type(user) == list:
        for u in user: 
            server.sendmail(fromaddrs, u, msg)
    else:
        server.sendmail(fromaddrs, user, msg)
    server.quit()
    return True
