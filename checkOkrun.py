#! /usr/bin/env python
# -*- coding: utf-8 -*-

# To get a logger for the script
try:
    from urllib.request import urlopen
    from urllib.parse import urlencode

    python_version = 3
except ImportError:
    from urllib2 import urlopen
    from urllib import urlencode

    python_version = 2

import sys
import json, logging, datetime, traceback
import time
sys.path.insert(0, "script")

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def json_request(url, data=None):
    if python_version == 3:
        return json_request_v3(url, data)
    else:
        return json_request_v2(url, data)


def json_request_v3(url, data=None):
    try:
        if not data:
            resp = urlopen(url)
            if python_version == 3:
                resp = resp.read()
        else:
            data = urlencode(data)
            resp = urlopen(url, data.encode('utf-8'))
            if python_version == 3:
                resp = resp.read()
        #print(resp)
        res = (True, json.loads(resp.decode('utf-8')))
    except Exception:
        traceback.print_exc()
        res = (False, '')
    return res


def json_request_v2(url, data=None):
    try:
        if not data:
            resp = urlopen(url).read()
        else:
            data = urlencode(data)
            resp = urlopen(url, data).read()
        #print(resp)
        res = (True, json.loads(resp))
    except Exception:
        traceback.print_exc()
        res = (False, '')
    return res

class TestJob():
    """testjob clase for cicd FIT/CST testing

        Attributes:


        Example:
            >>> testjob = TestJob(test_type, name, prefid, level, image_name, rerun)

        Methods:

        """

    def __init__(self,
                 jobid,
                 rerun = 0
                 ):
        """
                Args:
                    name: test job name
                    prefid: test job prefid stored in okrun

                """

        # Add attr here
        self.jobid = jobid
        #self.name = name
        #self.prefid = prefid
        #self.level = level
        #self.abort = False
        #self.image_name = image_name
        #self.rerun = rerun

    def submit(self, image_path, submitter, mailto):
        data = {
            'imagetftp': self.level,
            'imagepath': image_path,
            'mailto': mailto,
            'submitter': submitter,
            'prefid': self.prefid,
            'autoadd': 1
        }
        print('okrun data is: %s' % data)
        try:
            status, submit = json_request('http://10.74.21.84/index.php/jobsche/generatejob', data)
            print('status: %s, response: %s' % (status, submit))
            self.jobid = int(submit['jobid'])
            print('Submit job success, job id is: %s' % self.jobid)
            return True
        except Exception as e:
            traceback.print_exc()
            print(str(e))
            return False



    def query(self):
        # query if job is finished in okrun
        data = {
            "dir": "DESC",
            "filter[0][data][comparison]": "eq",
            "filter[0][data][type]": "numeric",
            "filter[0][data][value]": self.jobid,
            "filter[0][field]": "js.idJobsche",
            "filter[7][data][type]": "boolean",
            "filter[7][data][value]": "0",
            "filter[7][field]": "active",
            "filter[8][data][type]": "boolean",
            "filter[8][data][value]": "1",
            "filter[8][field]": "finished",
            "sort": "ftime"
        }
        
        # query if job is pending in okrun
        data_pending = {
            "dir": "DESC",
            "filter[0][data][comparison]": "eq",
            "filter[0][data][type]": "numeric",
            "filter[0][data][value]": self.jobid,
            "filter[0][field]": "js.idJobsche",
            "filter[7][data][type]": "boolean",
            "filter[7][data][value]": "0",
            "filter[7][field]": "active",
            "filter[8][data][type]": "boolean",
            "filter[8][data][value]": "0",
            "filter[8][field]": "finished",
            "sort": "ftime"
        }
        
        status, resp = json_request('http://okrun/index.php/jobsche/searchjobschevalidpaging', data_pending)
        while len(resp["jobsches"]) is not 0:
            sys.stdout.flush()
            #print("job is pending, wait for running")
            print('job id:%s is pending...'%(self.jobid))
            time.sleep(60)
            status, resp = json_request('http://okrun/index.php/jobsche/searchjobschevalidpaging', data_pending)
        
        i = 1
        status, resp = json_request('http://okrun/index.php/jobsche/searchjobschevalidpaging', data)
        while resp['totalCount'] == '0':
            sys.stdout.flush()
            print("poll job %s times"%i)
            try:
                status, resp = json_request('http://okrun/index.php/jobsche/searchjobschevalidpaging', data)
                #print(resp)
            except Exception as e:
                traceback.print_exc()
                print(str(e))
                
                return 1
            if 'totalCount' not in resp:
                print("job id:%s, okrun no response, try later"%(self.jobid))
                i+=1
                time.sleep(60)
            elif resp['totalCount'] == '0':
                print('job id:%s is running...'%(self.jobid))
                i+=1
                time.sleep(60)
            elif resp['totalCount'] == '1':
                break
                
        #if i>80:
        #    print('job more than 60 mins, timeout')
        #    self.result = 2    
            
        if resp['totalCount'] == '1':
            try:
                self.block = int(resp['jobsches'][0]['ats_block'])
            except Exception:
                self.block = 0
            try:
                self.error = int(resp['jobsches'][0]['ats_error'])
            except Exception:
                self.error = 0
            try:
                self.fail = int(resp['jobsches'][0]['ats_fail'])
            except Exception:
                self.fail = 0
            try:
                self.passed = int(resp['jobsches'][0]['ats_pass'])
            except Exception:
                self.passed = 0
            
            
            print("\n\n")
            print('=================================Job %s Summary==============================='
                  % (self.jobid))
            print('pass: %s, failed: %s, block: %s, error: %s' %(str(self.passed), str(self.fail), str(self.block), str(self.error)))
            print('Job report and log:')
            print('http://okrun/logviewer.php?idJobsche=%s' % self.jobid)
            print('=================================Job %s Summary==============================='
                  % (self.jobid))
            output = ''
            #if self.abort:
            #    output = "Job abort due to running timeout,link might not work: "
            self.link = output + 'http://okrun/logviewer.php?idJobsche=' + str(self.jobid)
            self.total = int(resp['jobsches'][0]['tcs'])+2
            if self.fail == 0 and self.block == 0 and self.error == 0:
                self.result = 0
            else:
                self.result = 1
            
            #if i>80:
            #    print('job timeout')
            #    self.result = 2
                
            return self.result
        
    def abort(self):
        ##todo
        pass    
        
if __name__ == '__main__':
    jobid = sys.argv[1]
    #def main():
    #    jobid = sys.argv[1]
    #    testjob = TestJob(jobid)
    #    result=testjob.query()
    #    print(result)
    #    
    #main()    
    testjob = TestJob(jobid)
    result = testjob.query()
    if result == 0:
        sys.exit(0)
    elif result == 1:
        sys.exit(1)
    else:
        sys.exit(2)
