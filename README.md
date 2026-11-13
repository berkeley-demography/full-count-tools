# full-count-tools

- first step is to transfer files from ipums:

`rclone backend copyid gdrive: {drive id} /global/scratch/p2p3/pl1_demography/ipums/{new-directory} --progress`

- next expand the zip files using 7z. Since it takes a long time it is a good idea to multiplex it to free up your screen. You will also want to get the 7z binary since it is not installed on savio: https://www.7-zip.org/download.html

`screen ./7zz x  IPUMS_1950_1.3.zip`

- Place this repo in the year to be processed and create MPC & TSV directories for each year. 

### parse person and household to TSV
`nohup python/parse2tsv.py MPC &`

to check progress
`tail nohup.out`

- When the files are done, move TSV files in the MPC directory to the TSV directory

### do file to R factors
`cat MPC/us1950b_usa_res.do | python/do2factor.py > factors1950.R`

### (optional) compress old .dat files to save space

`zstd -12 --long=31 -T16 us1880e_usa_res.dat -o us1880e_usa_res.dat.zst`

verify that the compression completed 

`zstd -t --long=31 us1880e_usa_res.dat.zst && echo "OK"`
