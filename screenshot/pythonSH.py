import sh
#sh.cd('..')
import path

KOLIBRI_DIR = path.abspath("../kolibri")
IMAGES_DIR = "gen-images"


#print(sh.ls('-l'))
sh.phantomjs('capture.js', 'urlstr', ...)
#sh.compare('')


#given an array of urls and branches automate screenshotting of them between different branches and create diff img

def genScreenshot(name, url):
	screenshotURL = url
	screenshotName = '{0}.jpeg'.format(name)
	sh.phantomjs('capture.js', url, path.join(IMAGES_DIR, screenshotName))

	comparisonIMG = 'exploreMasterLarge.jpeg'
	diffIMG = comparisonIMG + '_' + screenshotName + '.png'
	sh.compare(comparisonIMG + ' ' + screenshotName + ' ' + diffIMG)
	


states = [('explore', 'http://localhost:8000/learn/#/explore/5b1e904335ab4dfda82e3e37735262c5'), 
			('learn', 'http://localhost:8000/learn/#/learn/5b1e904335ab4dfda82e3e37735262c5')]

for stateTuple in states:
	genScreenshot(stateTuple[0], stateTuple[1])

# In [4]: git_dir = os.path.abspath(os.path.join('HookCatcherProj', '.git'))

# In [5]: working_dir = os.path.abspath('HookCatcherProj')

# In [6]: 

# In [6]: 

# In [6]: working_dir
# Out[6]: '/Users/mingdai/Documents/Python/HookCatcherProj'

# In [7]: git_dir
# Out[7]: '/Users/mingdai/Documents/Python/HookCatcherProj/.git'

#In [9]: sh.git('--git-dir', git_dir, '--work-tree', working_dir, 'status')
