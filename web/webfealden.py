import web
from web import form
import os
import pickle
import subprocess
import uuid

from fealden import searchserver, util, config

try:
    runtime = config.getconfig()
except config.ConfigError:
    sys.stderr.write("Unrecoverable error, exiting: %s\n" % errormsg)
    sys.exit()

render = web.template.render('templates/', base='layout')
urls = (
    '/', 'index',
    '/solution/(.+)', 'solution',
    '/solution_images/(.+)/(.+)', 'solution_images'
    )

app = web.application(urls,globals())

myform = form.Form(
    form.Textbox('recognition',form.notnull, form.regexp('^[ATGC]*$', 'DNA alphabet only: A, T, G, or C'), description="Recognition Sequence", id="recog"),
    form.Textbox('numfolds_lo', description='Lower bound for number of foldings in a valid solution', value=2, id="numfolds_lo"),
    form.Textbox('numfolds_hi', description='Upper bound for number of foldings in a valid solution', value=8, id="numfolds_hi"),
    form.Textbox('maxunknown_percent', description='Max percentage of folds that cannot be categorized', value=.1, id="maxunknown_percent"),
    form.Textbox('binding_ratio_lo', description='Lower bound for ratio of binding foldings vs. nonbinding foldings', value=.9, id="binding_ratio_lo"),
    form.Textbox('binding_ratio_hi', description='Upper bound for ratio of binding foldings vs. nonbinding foldings', value=1.1, id="binding_ratio_hi"),
    form.Textbox('maxenergy', description='Maximum additional energy (kJ/mol)', value=-5.0, id="maxenergy"),
    #    form.Textbox("email", description='(optional) email to recieve notifications at',
    #             id="email"),
    form.Button("Run", type="submit")
    )

class solution_images:
    def GET(self, recog, name):
        output_root = runtime.get("Locations", "solutions")
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
    def GET(self, unique_id):
        output_root = runtime.get("Locations", "solutions")
        # Check to see if output directory has been generated
        output_pickle = os.path.join(output_root,
                                     unique_id, "pickle.dat")
        if os.path.isfile(output_pickle):
            # Otherwise return template with solution
            (sensor, scores, folds) = pickle.load(open(output_pickle))
            return render.solution(sensor, scores, folds, unique_id)
        else:
            # Return templated HTML to keep trying
            return render.solution_retry(unique_id)
        

class index:
    def GET(self):
        form = myform()
        return render.formtest(form)

    def POST(self):
        # Validate form data
        form = myform()
        if not form.validates():
            # Bad validation => render the form again
            return render.formtest(form)

        # Otherwise start a new search
        email = False

        # Create directory for this solution to store its data
        unique_id = uuid.uuid4()
        output_root = runtime.get("Locations", "solutions")
        output_dir = os.path.join(output_root, unique_id.hex)
        os.makedirs(output_dir)

        # Add this request to the workqueue for fealdend
        output_pickle = os.path.join(output_dir, "pickle.dat")
        workqueue = runtime.get("Locations", "workqueue")
        q = util.DirectoryQueue(workqueue)

        # Clean up forms data to remove attr for the 'Run' button
        new_attrs = dict(form.d)
        del new_attrs["Run"]

        tofloats = [ "binding_ratio_lo", "binding_ratio_hi", "maxenergy", "maxunknown_percent" ]
        for el in tofloats:
            new_attrs[el] = float(new_attrs[el])

        toints = [ "numfolds_lo", "numfolds_hi"]
        for el in toints:
            new_attrs[el] = int(new_attrs[el])
        
        request = util.RequestElement(command="BACKTRACKING",
                                      request_id=unique_id.hex,
                                      output_dir=output_dir,
                                      maxtime=60,
                                      **new_attrs)
        q.put(request)

        # Send a http redirect to the solution
        raise web.seeother('/solution/' + unique_id.hex + '/')

if __name__ == "__main__":
    web.internalerror = web.debugerror
    app.run()
