These makefiles are recipes for several common tasks in different types of projects.
To add them to your project, simply do:

```
git remote add makefiles ssh://git@lab.cluster.gsi.dit.upm.es:2200/docs/templates/makefiles.git
git subtree add --prefix=.makefiles/ makefiles master
touch Makefile
echo "include .makefiles/base.mk" >> Makefile
```

Now you can take advantage of the recipes.
For instance, to add useful targets for a python project, just add this to your Makefile:

```
include .makefiles/python.mk
```

You may need to set special variables like the name of your project or the python versions you're targetting.
Take a look at each specific `.mk` file for more information, and the `Makefile` in the [senpy](https://lab.cluster.gsi.dit.upm.es/senpy/senpy) project for a real use case.

If you update the makefiles from your repository, make sure to push the changes for review in upstream (this repository):

```
make makefiles-push
```

It will automatically commit all unstaged changes in the .makefiles folder.
