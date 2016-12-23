# Export Evernote Notebooks & Stacks Into External Software
This script allows you to export all Evernote data (including notebooks & stacks) for the purpose of either backing up or importing into external software. 

I wrote this because there was no export/import solution for __notebooks & stacks__ (that is importable into external software) that I am aware of.

Basically the script exports all of your Evernote notes into a hierarchical directory structure based on your notebooks and notebook stacks. Additional features include converting all note syntax to markdown text or Zim Wiki syntax (to import into Zim Wiki).



Why Import to Zim Wiki? (Optional)
----------------------------------
It is the most simple, intuitive, linux friendly, offline, semi-markdown compatible note taking app. (If you miss sync features, then just use your preferred cloud setup for that instead.)


How it works
-------------
* Queries your local Evernote database to grab all the notebooks and notebook stacks associated with your notes.
* Recursively walks the directory tree (of your exported Evernote backup) and does the following:
    * creates proper notebook structure & organizes your notes accordingly (based on your Evernote's database mapping)
        * copies all the notes to their respective folder (notebook) or nested folder (stack + notebook)
        * notes that do not belong to a notebook are copied into a directory named "uncategorized"
    * _(optionally)_ converts the html within files to markdown text, 
    * _(optionally)_ further convert the notes to be importable into Zim wiki, which will do the following:
        * further modifies lists, headings, and images in order to comply with zim syntax
        * replaces all forbidden characters in filenames and directories (which are used as page names) with underscores
        * replaces .html file extension with .txt


Instructions
------------

Since Evernote does not natively allow you to export all notebook data (stacks/notebooks). You have to make sure to provide this script with the location of your Evernote database file.

1. if you haven't already, install the Evernote desktop client (in a VM if needed)
    * make sure your data is synced
    * In the top left side panel, right click "Notebooks" > "Export notes", to export all your notes 
2. prepare and run the script by doing the following:
    * input the full path where your exported Evernote data resides
    * input the full path where your Evernote database file resides (i.e; "your_username.exb")
    * input the new path where you want to save all your newly constructed Evernote data
    * run it
 
3. **(Optional)** Import data into Zim Wiki:
    * click File > Open Another notebook, and select the folder where your converted Evernote data is.
    * optionally, you may set it as the Default notebook in the dropdown.

    > *"Rebuilding the index in may take quite some time, if you have added many pages. 
    > It may be advisable to click Tools / Re-build Index" - http://zim-wiki.org/manual/Help/Importing_external_files.html*


Rant
----
Due to evernotes sheer carelessness / lack of consideration in not including notebooks/stacks with exported data. Soon after realizing that I will need the local Evernote database in order to grab the notebook/stack data, I wasted nearly an entire day trying to recover it from slack space on my drives (far from successful), though luckily I managed to find it on an old drive....Thanks you Evernote.


Credits
-------

* html2text.py module by Aaron Swartz
    * https://github.com/aaronsw/html2text