# full-count-tools

place this repo in the year to be processed

### parse person and household to TSV
`nohup python/parse2tsv.py MPC &`

to check progress
`tail nohup.out`

### do file to R factors
`cat MPC/us1950b_usa_res.do | python/do2factor.py > factors1950.R`
