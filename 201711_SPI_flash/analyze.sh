#!/bin/bash

src()
{
  zcat flash_erase_20171111.csv.Z
}

analyzer()
{
    awk -e '
BEGIN { width = 8; i = 0; prev=""; repeat=0; }
function flush_all()
{
  if (repeat == 1) {
    printf("%11.6f %5s %s \n", prev_ts, name, prev)
  } else if (1 < repeat) {
    printf("%11.6f %5s            : (%d times)\n", prev_ts, "", repeat)
  }
  repeat=0
}
function flush()
{
if (i <=0)
  return
buf=""
buf = sprintf("%s%32s ", buf, cmd)
for (j=0; j<i; j++)
  buf = sprintf("%s%s ", buf, mosi[j])
for ( ; j<width; j++)
  buf = sprintf("%s   ", buf)
buf = sprintf("%s: ", buf)
for (j=0; j<i; j++)
  buf = sprintf("%s%s ", buf, miso[j])
for ( ; j<width; j++)
  buf = sprintf("%s   ", buf)
i=0
if (buf == prev) {
  repeat++
  prev_ts=ts[0]
} else {
  flush_all()
  printf("%11.6f %5s %s \n", ts[0], name, buf)
}
prev=buf
}
/[0-9.],SPI,MOSI:/ {
ts[i]=gensub(/(^[0-9.]*),(.*),(.*)/, "\\1", "g", $1)
 name=gensub(/(^[0-9.]*),(.*),(.*)/, "\\2", "g", $1)
mosi[i]=gensub("\\(0x([0-9A-F][0-9A-F])\\);", "\\1", "g", $3)
miso[i]=gensub("\\(0x([0-9A-F][0-9A-F])\\)", "\\1", "g", $6)
i++
if (i == 1)
  switch (mosi[0]) {
  case /05/: len=2; cmd="RDSR1 (Read Status Register 1)"; break;
  case /05/: len=1; cmd="BE (Bulk Erase)"; break;
  default:   len=1; cmd=""; break;
  }
if (i == len)
  flush()
next
}
{
  flush()
  printf("# %s\n", $0)
}
END{
  flush(); 
  flush_all();
}
'
}

src |  analyzer
