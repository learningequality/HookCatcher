import sh
#sh.cd('..')


#print(sh.ls('-l'))
sh.phantomjs('capture.js http://localhost:8000/learn/#/explore/5b1e904335ab4dfda82e3e37735262c5 explore.jpeg')
#sh.compare('')


# arrayURL = [['explore', 'http://localhost:8000/learn/#/explore/5b1e904335ab4dfda82e3e37735262c5'], 
# 			['learn', 'http://localhost:8000/learn/#/learn/5b1e904335ab4dfda82e3e37735262c5']]

# #given an array of urls and branches automate screenshotting of them between different branches and create diff img

# for idxURL in range(len(arrayURL)):
# 	print("name of state:" + arrayURL[idxURL][1])
# 	screenshotURL = arrayURL[idxURL][1]
# 	screenshotName = arrayURL[idxURL][0]+ '.jpeg'#explore_test-pr
# 	print('capture.js ' + screenshotURL + ' ' + screenshotName)
# 	sh.phantomjs('capture.js ' + screenshotURL + ' ' + screenshotName)

# 	comparisonIMG = 'exploreMasterLarge.jpeg'
# 	diffIMG = comparisonIMG + '_' + screenshotName + '.png'
# 	sh.compare(comparisonIMG + ' ' + screenshotName + ' ' + diffIMG)