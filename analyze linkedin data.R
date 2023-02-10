library(dplyr)
library(ggplot2)

setwd("C:/Users/VNFSK/Downloads")

df <- read.csv(file.choose(), stringsAsFactors = F)

str(df)


df$Date <- as.Date(df$Date, "%m/%d/%Y")

df$DaysAgo <- as.numeric(Sys.Date() - df$Date)


ggplot(df, aes(x = DaysAgo)) + geom_histogram(breaks = 1:max(df$DaysAgo), bins = 10) + scale_x_continuous(breaks = seq(0, 190, 15))
table(df$DaysAgo[df$DaysAgo < 8])
