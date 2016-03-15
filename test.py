
import requests
import zipfile
from io import BytesIO
import StringIO, pickle, csv
import thread
import time
from sets import Set
import pycurl
import cStringIO
import json
import datetime

request_url = "http://route.cit.api.here.com/routing/7.2/calculateroute.json?app_id=oxFV8daRXZafXLI87l7o&app_code=1Af5pCupGbm6NrfnWxPDsg&mode=fastest;publicTransport&waypoint0=geo!36.166035,-86.807027&waypoint1=geo!36.164271,-86.804409&waypoint2=geo!36.16532,-86.783168&waypoint3=geo!36.165367,-86.783041&waypoint4=geo!36.165549,-86.782606&waypoint5=geo!36.165851,-86.781893&waypoint6=geo!36.166126,-86.782064&waypoint7=geo!36.166409,-86.78224&waypoint8=geo!36.166454,-86.782268&waypoint9=geo!36.166959,-86.782592&waypoint10=geo!36.167655,-86.78304&waypoint11=geo!36.167855,-86.783166&waypoint12=geo!36.164105,-86.804291&waypoint13=geo!36.168254,-86.782151&waypoint14=geo!36.168229,-86.782111&waypoint15=geo!36.168104,-86.78194&waypoint16=geo!36.168013,-86.781827&waypoint17=geo!36.167913,-86.781722&waypoint18=geo!36.167834,-86.781642&waypoint19=geo!36.167255,-86.781269&waypoint20=geo!36.167102,-86.781165&waypoint21=geo!36.166918,-86.781043&waypoint22=geo!36.166762,-86.781413&waypoint23=geo!36.164016,-86.804228&waypoint24=geo!36.166763,-86.781413&waypoint25=geo!36.166659,-86.781668&waypoint26=geo!36.166561,-86.781901&waypoint27=geo!36.163873,-86.804129&waypoint28=geo!36.163773,-86.804058&waypoint29=geo!36.163222,-86.803689&waypoint30=geo!36.162843,-86.803422&waypoint31=geo!36.162496,-86.803179&waypoint32=geo!36.162245,-86.803007&waypoint33=geo!36.162182,-86.802963&waypoint34=geo!36.16629,-86.805339&waypoint35=geo!36.162099,-86.802905&waypoint36=geo!36.162026,-86.802854&waypoint37=geo!36.161927,-86.802786&waypoint38=geo!36.16187,-86.802747&waypoint39=geo!36.161659,-86.802608&waypoint40=geo!36.161564,-86.802545&waypoint41=geo!36.161532,-86.802526&waypoint42=geo!36.161325,-86.802388&waypoint43=geo!36.16128,-86.80236&waypoint44=geo!36.160993,-86.802158&waypoint45=geo!36.165746,-86.80511&waypoint46=geo!36.160749,-86.801994&waypoint47=geo!36.160523,-86.801853&waypoint48=geo!36.160774,-86.801271&waypoint49=geo!36.160992,-86.800758&waypoint50=geo!36.161132,-86.800433&waypoint51=geo!36.161354,-86.799911&waypoint52=geo!36.16155,-86.799453&waypoint53=geo!36.161753,-86.798973&waypoint54=geo!36.161781,-86.798907&waypoint55=geo!36.161861,-86.798715&waypoint56=geo!36.165645,-86.805066&waypoint57=geo!36.161915,-86.798593&waypoint58=geo!36.162171,-86.798009&waypoint59=geo!36.162215,-86.797915&waypoint60=geo!36.162453,-86.79735&waypoint61=geo!36.162593,-86.797019&waypoint62=geo!36.162611,-86.796974&waypoint63=geo!36.162763,-86.796608&waypoint64=geo!36.162953,-86.796147&waypoint65=geo!36.162999,-86.796043&waypoint66=geo!36.163418,-86.795103&waypoint67=geo!36.165266,-86.804916&waypoint68=geo!36.163455,-86.795021&waypoint69=geo!36.163747,-86.794386&waypoint70=geo!36.163851,-86.794157&waypoint71=geo!36.163996,-86.793887&waypoint72=geo!36.164026,-86.793833&waypoint73=geo!36.164061,-86.79377&waypoint74=geo!36.164094,-86.793702&waypoint75=geo!36.164121,-86.793645&waypoint76=geo!36.164249,-86.793305&waypoint77=geo!36.164657,-86.792351&waypoint78=geo!36.164944,-86.804787&waypoint79=geo!36.164736,-86.792172&waypoint80=geo!36.164232,-86.791863&waypoint81=geo!36.164044,-86.791731&waypoint82=geo!36.163679,-86.791471&waypoint83=geo!36.163443,-86.791317&waypoint84=geo!36.163286,-86.791214&waypoint85=geo!36.162923,-86.790947&waypoint86=geo!36.162738,-86.790814&waypoint87=geo!36.162623,-86.790782&waypoint88=geo!36.162474,-86.790732&waypoint89=geo!36.16479,-86.804726&waypoint90=geo!36.162351,-86.790691&waypoint91=geo!36.162221,-86.790653&waypoint92=geo!36.162169,-86.790639&waypoint93=geo!36.162116,-86.790624&waypoint94=geo!36.162378,-86.790021&waypoint95=geo!36.162502,-86.789738&waypoint96=geo!36.16291,-86.788838&waypoint97=geo!36.162999,-86.788668&waypoint98=geo!36.163017,-86.788629&waypoint99=geo!36.163252,-86.78818&waypoint100=geo!36.164637,-86.804645"
buf = cStringIO.StringIO()
c = pycurl.Curl()
c.setopt(c.URL, request_url)
c.setopt(c.WRITEFUNCTION, buf.write)
# stdout.append("request_url beforeperform")
c.perform()
# stdout.append("request_url perform")
response_string = buf.getvalue()
print response_string