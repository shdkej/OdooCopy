#/bin/bash
filename=$(ls -tr | tail -5 | grep [0-9]_)
GREEN='\033[0;32m'
NC='\033[0m'
echo -n "${GREEN}DB명을 입력해주세요(미입력시 gvm) :${NC}"
read input
dbname="$input"
if [ -z $input ]
then
    dbname="gvm"
fi
BackupPath="/var/lib/odoo"
echo ${filename}
unzip ${filename} -d ${BackupPath}/backups
echo "db:5432:*:$USER:$PASSWORD" >> /root/.pgpass
chmod 0600 /root/.pgpass
createdb -h db -U odoo -w ${dbname}
psql -h db -U odoo -w ${dbname} < ${BackupPath}/backups/dump.sql
psql -h db -U odoo -w ${dbname} -c "DELETE FROM ir_attachment WHERE url LIKE '/web/content/%'"
mkdir -p ${BackupPath}/filestore/${dbname}
chown -R odoo:odoo ${BackupPath}
mv ${BackupPath}/backups/filestore/* ${BackupPath}/filestore/${dbname}
echo "##데이터 백업 완료##"
echo "${GREEN}소스코드 업데이트를 하시겠습니까? (y or n)${NC}"
read check_update
if [ $check_update = "n" ]
then
    echo "${GREEN}##데이터 업데이트 완료##${NC}"
    break
fi
git stash clear
git stash
git pull origin master
git stash drop
echo "##소스코드 업데이트 완료##"
cp config.ini.example config.ini
odoo --db_host db -r $USER -w $PASSWORD -d ${dbname} -u analytic,gvm,gvm_mrp,hr,hr_attendance,product,project,purchase
echo "${GREEN}##최신버전 업데이트 완료##${NC}"
