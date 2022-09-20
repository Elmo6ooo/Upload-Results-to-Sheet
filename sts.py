import gspread
import requests as req
import time
from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials
from gspread.cell import Cell


with open("/usr/local/google/home/chienliu/Downloads/android-sts/results/2022.09.07_10.30.16/test_result_failures_suite.html") as fp:
    soup = BeautifulSoup(fp, 'html')

scopes = ["https://spreadsheets.google.com/feeds"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scopes)
client = gspread.authorize(credentials)
sheet = client.open_by_key("1eSp4g_2Z86MnZLUVljhMoDt1OgRIPeEV0KYMVq22zag").worksheet("TM-Seahawk-STS")	

#crawl data and keep it in result as string list
rows = soup.find("table", {"class": "testsummary"}).find_all("tr")
result = []
for row in rows:	
	for i in row.find_all('td'):
		result.append(str(i).replace('<td>', '').replace('</td>',''))

#keeps data that we want to upload
cells = []

#col in dict
dic = {}
col = sheet.col_values(2)
for i in range(3):
	col.pop(0)
index = 4
for i in col:
	dic[i] = index
	index = index + 1

#0:Module, 1:Passed, 2:Failed, 3:Assumption Failure, 4:Ignored, 5:Total Tests, 6:Done
for i in range(0, len(result), 7):
	#remove unnecessary data from Module
	if "href" in result[i]:
		tmp = result[i].split(">")
		result[i] = tmp[1].replace('arm64-v8a ','').replace('</a','')
	else:
		tmp = result[i].split()
		result[i] = tmp[1]

	#data to upload
	if result[i] in dic:
		cells.append(Cell(dic[result[i]], 3, result[i+5]))
		if result[i+2] != '0' and result[i+6] == 'true':
			cells.append(Cell(dic[result[i]], 4, result[i+2]))
			cells.append(Cell(dic[result[i]], 9, 'FAIL'))
		elif result[i+6] == 'false':
			cells.append(Cell(dic[result[i]], 9, 'INCOMPLETE'))
		elif result[i+3] == result[i+4] and result[i+3] == result[i+5]:
			cells.append(Cell(dic[result[i]], 9, 'REMOVED'))
		elif result[i+4] == result[i+5] and result[i+4] != '0':
			cells.append(Cell(dic[result[i]], 9, 'Ignored'))
		elif result[i+3] != '0' and (result[i+3] == result[i+5] or int(result[i+3])+int(result[i+4]) == int(result[i+5])):
			cells.append(Cell(dic[result[i]], 9, 'Assumption'))
		else:
			cells.append(Cell(dic[result[i]], 9, 'PASS'))		
	else:
		print("not found: %s" %result[i])
		
#upload data	
sheet.update_cells(cells)

print("DONE")	


'''
#for finding data
cell = sheet.find('apple')
if not cell:
	print("not found")
#for update data (row, col, data) works on fill data and change status
sheet.update_cell(35, 8, 'PASS')

#update multiple cells
cells = []
cells.append(Cell(row=34, col=3, value=52))
cells.append(Cell(row=35, col=3, value=20))
sheet.update_cells(cells)
'''	
	
