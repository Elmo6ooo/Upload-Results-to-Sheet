import gspread
import sys
from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials
from gspread.cell import Cell

def upload_cts(soup, sheet, dic, incompletes, cmds, fw, row_count, cells, cells2, not_found):
	# combine [instant] into the parent test ?? other[...]
	i = 0
	while i < len(cmds)-1:	
		if i != len(cmds)-2 and cmds[i] == cmds[i+2]:
			cmds[i+1] += cmds[i+3] + " "
			del cmds[i+2:i+4]
		i += 2
	
	# crawl data and keep it in result as string list
	rows = soup.find("table", {"class": "testsummary"}).find_all("tr")
	result = []
	k = 0
	for row in rows:
		if "Module" in str(row):
			continue
		r = []
		j = 0
		for i in row.find_all('td'):
			r.append(str(i).replace('<td>', '').replace('</td>',''))
			j = j+1 
		result.append(r)
		k = k+1
	
	#remove href & arm64-v8a
	for i in range(len(rows)-1):
		if "href" in result[i][0]:
			tmp = result[i][0].split(">")
			result[i][0] = tmp[1].replace('arm64-v8a ','').replace('</a','')
		else:
			tmp = result[i][0].split()
			result[i][0] = tmp[1]
	
	#0:Module, 1:Passed, 2:Failed, 3:Assumption Failure, 4:Ignored, 5:Total Tests, 6:Done
	while result:
		family = []
		family.append(0)
		i = 0 #constant
		j = 1 #check later result family or not
		while len(result) > 1:
			if len(result) <= j:	break
			elif result[i][0]+"[instant]" == result[j][0] or \
			result[i][0]+"[run-on-secondary-user]" == result[j][0] or \
			result[i][0]+"[run-on-work-profile]" == result[j][0] or \
			result[i][0]+"[run-on-clone-profile]" == result[j][0]:	
				family.append(j)
			if j == 20:	break
			else:	j = j+1
				
		P, F, A, I, T, D = (0,0,0,0,0,True)
		for k in family:		
			P = P + int(result[k][1])
			F = F + int(result[k][2])
			A = A + int(result[k][3])
			I = I + int(result[k][4])
			T = T + int(result[k][5])
			if result[k][6] == "false":
				D = False
			
		M = result[i][0]
		for k in reversed(family):
			result.pop(k)
		family.clear()

		# Add not found into dic
		if M not in dic:
			row_count += 1
			dic[M] = row_count
			sheet.append_row([M],table_range="A"+str(row_count))
			not_found.append(M)

		cells.append(Cell(dic[M], 2, T))			
		if F != 0 and D:
			cells.append(Cell(dic[M], 3, F))
			cells.append(Cell(dic[M], 4, 'FAIL'))		
		elif not D:
			cells.append(Cell(dic[M], 4, 'INCOMPLETED'))
		elif A == I and A == T:
			cells.append(Cell(dic[M], 4, 'NO RESULT'))
		elif I == T and I != 0:
			cells.append(Cell(dic[M], 4, 'IGNORED'))
		elif A != 0 and (A == T or A+I == T):
			cells.append(Cell(dic[M], 4, 'ASSUMPTION'))
		else:
			cells.append(Cell(dic[M], 4, 'PASS'))
		
		# find module and upload command
		if cmds and M == cmds[0]:
			
			# if failed == total tests then just filter the module
			if F == T:
				cells2.append(Cell(dic[M], 5, "--include-filter \"" + cmds[0] + "\""))
			else:
				cells2.append(Cell(dic[M], 5, cmds[1]))
			del cmds[0:2]

			# cells can only upload maximum 50000 char at once
			if sum(len(str(i)) for i in cells2) > 30000:
				sheet.update_cells(cells2)
				cells2.clear()

		# the rest of incomplete modules		
		if incompletes and M == incompletes[0]:
			fw.write("--include-filter \"" + incompletes[0] + "\" \n")
			cells2.append(Cell(dic[M], 5, "--include-filter \"" + incompletes[0] + "\""))
			del incompletes[0]

def upload_other(soup, sheet, dic, incompletes, cmds, fw, row_count, cells, cells2, not_found):
	# crawl data and keep it in result as string list
		rows = soup.find("table", {"class": "testsummary"}).find_all("tr")
		result = []
		for row in rows:	
			for i in row.find_all('td'):
				result.append(str(i).replace('<td>', '').replace('</td>',''))

		# 0:Module, 1:Passed, 2:Failed, 3:Assumption Failure, 4:Ignored, 5:Total Tests, 6:Done
		for i in range(0, len(result), 7):
			# remove unnecessary data from Module
			if "href" in result[i]:
				tmp = result[i].split(">")
				result[i] = tmp[1].replace('arm64-v8a ','').replace('</a','')
			else:
				tmp = result[i].split()
				result[i] = tmp[1]

			M = result[i]

			# Add not found into dic
			if M not in dic:
				row_count += 1
				dic[M] = row_count
				sheet.append_row([M],table_range="A"+str(row_count))
				not_found.append(M)
				
			# data to upload
			cells.append(Cell(dic[M], 2, int(result[i+5])))
			if result[i+2] != '0' and result[i+6] == 'true':
				cells.append(Cell(dic[M], 3, int(result[i+2])))
				cells.append(Cell(dic[M], 4, 'FAIL'))
			elif result[i+6] == 'false':
				cells.append(Cell(dic[M], 4, 'INCOMPLETED'))
			elif result[i+3] == result[i+4] and result[i+3] == result[i+5]:
				cells.append(Cell(dic[M], 4, 'NO RESULT'))
			elif result[i+4] == result[i+5] and result[i+4] != '0':
				cells.append(Cell(dic[M], 4, 'IGNORED'))
			elif result[i+3] != '0' and (result[i+4] == result[i+5] or int(result[i+3])+int(result[i+4]) == int(result[i+5])):
				cells.append(Cell(dic[M], 4, 'ASSUMPTION'))
			else:
				cells.append(Cell(dic[M], 4, 'PASS'))

			# find module and upload command
			if cmds and M == cmds[0]:

				# if failed == total tests then just filter the module
				if result[i+2] == result[i+5]:
					cells2.append(Cell(dic[M], 5, "--include-filter \"" + cmds[0] + "\""))
				else:
					cells2.append(Cell(dic[M], 5, cmds[1]))
				del cmds[0:2]

				# cells can only upload maximum 50000 char at once
				if sum(len(str(i)) for i in cells2) > 30000:
					sheet.update_cells(cells2)
					cells2.clear()

			# the rest of incomplete modules
			if incompletes and M == incompletes[0]:
				fw.write("--include-filter \"" + incompletes[0] + "\" \n")
				cells2.append(Cell(dic[M], 5, "--include-filter \"" + incompletes[0] + "\""))
				del incompletes[0]

def upload(test_suite, build, device, path, clear):
	sheet = build.upper() + "-" + device.upper() + "-" +test_suite.upper()
	with open(path) as fp:
		soup = BeautifulSoup(fp, 'lxml')

	scopes = ["https://spreadsheets.google.com/feeds"]
	credentials = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scopes)
	client = gspread.authorize(credentials)
	sheet = client.open_by_key("1eSp4g_2Z86MnZLUVljhMoDt1OgRIPeEV0KYMVq22zag").worksheet(sheet)

	# Not found (return value)
	row_count = sheet.row_count
	not_found = []

	# clear previous sheet result
	if clear:
		sheet.batch_clear(['B:E'])

	# keeps data that we want to upload
	cells = []		# basic results
	cells2 = []		# commands

	# create module dictionary
	dic = {}
	col = sheet.col_values(1)
	index = 1
	for i in col:
		dic[i] = index
		if clear:
			cells.append(Cell(dic[i], 4, 'REMOVE'))
		index = index + 1
	
	# get all module from testsummary
	all_module = []
	tests = soup.find("table", {"class": "testsummary"}).find_all("tr")
	for test in tests:
		if "Module" in str(test):
			continue
		for i in test.find_all('td'):
			if len(i.contents[0]) > 10:
				all_module.append(i.contents[0].split()[1])
			elif len(str(i)) > 20:
				all_module.append(str(i).split()[2].split('<')[0])

	# parse incompletemodules
	incompletes = []
	try:
		modules = soup.find('table', 'incompletemodules').find_all('td')
		for module in modules:
			module = module.contents[0].contents[0].split()[1]
			tmodule = module.replace("[instant]","").replace("[run-on-secondary-user]","") \
				.replace("[run-on-work-profile]","").replace("[run-on-clone-profile]","")
			if tmodule in all_module and tmodule not in incompletes:
				incompletes.append(tmodule)
			elif tmodule in all_module and tmodule in incompletes:
				next
			elif module not in incompletes:
				incompletes.append(module)
	except: pass
	backup_incompletes = incompletes.copy()
	
	# keep all commands
	cmds = []
	fw = open('./cmds','w')

	# parse testdetails turn into --include-filter, if incomplete just filter module
	tests = soup.find_all('table', 'testdetails')
	for test in tests:
		cmd = ""
		module = test.find('td', 'module').contents[0].contents[0].split()[1]
		tmodule = module.replace("[instant]","").replace("[run-on-secondary-user]","") \
			.replace("[run-on-work-profile]","").replace("[run-on-clone-profile]","")
		try: # combine child module to parent if there is one
			if tmodule in all_module or tmodule in incompletes:
				module = tmodule
		except: pass

		if module in incompletes:
			cmd += "--include-filter \"" + module + "\" "
			incompletes.remove(module)
		else:
			testcases = test.find_all('td', 'testname')
			for tc in testcases:
				cmd += "--include-filter \"" + module + " " + tc.contents[0] + "\" "
		try:
			if cmds[-2] and module != cmds[-2]:
				fw.write('\n')
		except: pass

		if module not in cmds:
			cmds.append(module)
			cmds.append(cmd)
			fw.write(cmd)
		elif module not in backup_incompletes and module == cmds[-2]:
			dif_testcase = cmd.split("\"")
			for i in range(1,len(dif_testcase),2):
				if dif_testcase[i] not in cmds[-1]:
					cmds[-1] += "--include-filter \""+dif_testcase[i]+ "\" "
					fw.write("--include-filter \""+dif_testcase[i]+ "\" ")
	fw.write('\n')

	if test_suite == "CTS":
		upload_cts(soup, sheet, dic, incompletes, cmds, fw, row_count, cells, cells2, not_found)
	else:
		upload_other(soup, sheet, dic, incompletes, cmds, fw, row_count, cells, cells2, not_found)
	
	fw.close()

	#upload data	
	sheet.update_cells(cells)
	sheet.update_cells(cells2)

	return not_found

if len(sys.argv) > 1:
	device = sys.argv[1].upper()
	build = sys.argv[2].upper()
	test_suite = sys.argv[3].upper()
	path = sys.argv[4]

else:
	print("Which device (sh, ...)")
	device = input().upper()
	print("Which build (tm, udc, ...)")
	build = input().upper()
	print("Which testsuite (cts,gsi, ...)")
	test_suite = input().upper()
	print("Results path (/usr/...)")
	path = input()

upload_result = upload(test_suite, build, device, path, True)
print("Not Found: ")
print(upload_result)
print("DONE")
