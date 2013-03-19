import web
from web import form
import os
import pickle
import subprocess

from fealden import searchserver, util

render = web.template.render('templates/', base='layout')
urls = (
    '/', 'index',
    '/solution/(.+)', 'solution',
    '/solution_images/(.+)/(.+)', 'solution_images'
    )

app = web.application(urls,globals())

myform = form.Form(
    form.Textbox('Recognition Sequence',form.notnull, form.regexp('^[ATGC]*$', 'DNA alphabet only: A, T, G, or C'), description="Recognition", id="recog"),
    #    form.Textbox("email", description='(optional) email to recieve notifications at',
    #             id="email"),
    form.Button("Run", type="submit")
    )

class solution_images:
    def GET(self, recog, name):
        output_root = "/var/fealden/solutions/"
        filename, ext = os.path.splitext(name)

        cType = {
            ".png":"image/png",
            ".jpg":"image/jpeg",
            ".gif":"image/gif",
            ".ico":"image/x-icon"            }

        if name in os.listdir(os.path.join(output_root, recog)):
            web.header("Content-Type", cType[ext])
            return open(os.path.join(output_root,recog,name), "rb").read()
        else:
            raise web.notfound()

class solution:
    def GET(self, recognition):
        output_root = "/var/fealden/solutions/"
        # Check to see if output directory has been generated
        output_pickle = os.path.join(output_root,
                                     recognition, "pickle.dat")
        if os.path.isfile(output_pickle):
            # Otherwise return template with solution
            (sensor, scores, folds) = pickle.load(open(output_pickle))
            return render.solution(sensor, scores, folds)
        else:
            # Return templated HTML to keep trying
            return render.solution_retry(recognition)
        

class index:
    def GET(self):
        form = myform()
        return render.formtest(form)

    def POST(self):
        # Validate form data
        form = myform()
        if not form.validates():
            return render.formtest(form)
        recog = form['Recognition Sequence'].value
        #email = form['email'].value
        email = False
        # If solution has not been generated, 
        # run fealden again

        output_root = "/var/fealden/solutions/"
        output_dir = os.path.join(output_root, recog)

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        output_pickle = os.path.join(output_dir, "pickle.dat")

        if not os.path.isfile(output_pickle):
            # Add this request to the workqueue for fealdend
            workqueue = "/var/fealden/workqueue"
            q = util.DirectoryQueue(workqueue)
            request = util.RequestElement(command="BACKTRACKING",
                                          recognition=recog,
                                          output_dir=output_dir,
                                          email=email,
                                          maxtime=60)
            q.put(request)
            # # Create a new process to run fealden.web_output()
            # # This will run asynchronously, letting this process
            # # complete and redirect.
            # subprocess.Popen(["nohup python fealden.py -w -i %s -e %s &" % (recog, email)],
            #                  shell=True,
            #                  stdout=subprocess.PIPE,
            #                  stderr=subprocess.STDOUT)

        # In both cases, send a http redirect to the solution
        raise web.seeother('/solution/' + recog + '/')

if __name__ == "__main__":
    web.internalerror = web.debugerror
    app.run()
