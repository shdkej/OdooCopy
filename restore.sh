#/bin/bash
filename=$(ls -tr /var/lib/odoo/backups | tail -1)
dbname="test4"
BackupPath="/var/lib/odoo/backups"
echo ${filename}
unzip ${BackupPath}/${filename} -d ${BackupPath}
createdb -h db -O odoo -U odoo ${dbname}
psql -h db ${dbname} -U odoo < ${BackupPath}/dump.sql
mkdir ${BackupPath}/${dbname}
cp -r ${BackupPath}/filestore/* ${BackupPath}/${dbname}
