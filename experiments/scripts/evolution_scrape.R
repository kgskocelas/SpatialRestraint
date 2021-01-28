# Scrapes *evolution* data into a usable .csv file

rm(list = ls())
library(hash)

#### BEGIN CONFIGURATION ####

# A .txt file, each line is a slurm output file we will scrape
file_list_filename = 'files_to_scrape.txt'
# Where to save the output .csv?
output_filename = 'data_spatial_restraint_start_75.csv'
# This one's tricky
# If we have a filename eg. /mnt/gs18/scratch/users/bob/MCSIZE_512__ONES_70/101/slurm.out
# We split it on the character /
# We need the index into that split that has the infromation (here MCSIZE_512...)
# Remember, R starts at index 1, and there is technically an empty string before /
# Therefore, for the abox example we'd need a value of 7
filename_focal_idx = 10
# How many generations to skip between records? (1 = all records & a huge file)
gen_step = 100
# What are the maximum and minimum generations?
gen_min = 0
gen_max = 5000
gen_count = (gen_max - gen_min) + 1
gen_count_actual = (gen_max - gen_min) / gen_step + 1
# How many replicates exist *in each file*?
rep_count = 100

#### END CONFIGURATION ####

# Sources: 
# https://stackoverflow.com/questions/4106764/what-is-a-good-way-to-read-line-by-line-in-r

filename_vec = as.character(read.csv(file_list_filename, header = F)[,1])
# Don't initialize data until we read the first file
data = NA
data_initialized = F

options(warn = 1)
for(filename_idx in 1:length(filename_vec)){
    # Get the next filename, and extract all information embedded in it
    filename = filename_vec[filename_idx]
    filename_parts = strsplit(strsplit(filename, '/')[[1]][filename_focal_idx], '__')
    filename_var_hash = hash()
    filename_vars = c()
    for(filename_part in filename_parts[[1]]){
        filename_bits = strsplit(filename_part, '_')
        if(filename_bits[[1]][1] != 'spatial'){
            filename_vars = c(filename_vars, filename_bits[[1]][1])
            filename_var_hash[[filename_bits[[1]][1]]] = filename_bits[[1]][2]
        }
    }
    cat(filename, '\n')
    print(filename_vars)
    print(filename_var_hash)
    cat(filename, '\n')
    # Read the file!
    fp = file(filename, open = 'r')
    rep_id = 1
    line_num = 1
    # Keep reading until we hit an empty line
    while(length(line <- readLines(fp, n = 1, warn = F)) > 0){
        # Check to see if this line is starting a new replicate
        parts_list = strsplit(line, ' ')
        if(!is.na(parts_list[[1]][1]) && parts_list[[1]][1] == 'START'){
            # Start prepping data for this replicate
            rep_id = as.numeric(parts_list[[1]][length(parts_list[[1]])])
            print(rep_id)
            # Load *only* the data for this replicate, but do it all at once
            data_rep = read.csv(filename, skip = line_num, nrow = gen_count, header = T)
            colnames(data_rep) = c('generation', 'ave_ones', 'ave_repro_time')
            data_rep$generation = as.numeric(data_rep$generation)
            data_rep = data_rep[data_rep$generation %% gen_step == 0,]
            data_rep$rep_id = rep_id
            for(var in filename_vars){
                data_rep[,var] = filename_var_hash[[var]]
            }
            # If data isn't initialized, initialize it here (with the sizes we now know)
            if(!data_initialized){
                data = data.frame(data = matrix(
                    nrow = rep_count * gen_count_actual * length(filename_vec), 
                    ncol = ncol(data_rep)))
                colnames(data) = colnames(data_rep)
                data_initialized = T
            }
            # Figure out where this replicate will go in the overarching data frame
            # filename_idx is 1-indexed, rep_id is 0-indexed
            start_idx = (filename_idx - 1) * rep_count * gen_count_actual + rep_id * gen_count_actual
            stop_idx =  (filename_idx - 1) * rep_count * gen_count_actual + (rep_id + 1) * gen_count_actual - 1
            cat(start_idx, ':', stop_idx, '\n')
            # Insert the data!
            data[start_idx:stop_idx,] = data_rep
            line <- readLines(fp, n = gen_count + 1, warn = F)
            line_num = line_num + 2 + gen_count # This line + header + data
        }
        # Else this is not starting a replicate, move onto the next line
        else{
            line_num = line_num + 1
        }
    }
}
# Output the data! :^)
write.csv(data, output_filename)
cat(paste0('Done! File saved to: ', output_filename, '!', '\n'))