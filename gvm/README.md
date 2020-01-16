---


---

<h1 id="gvm">gvm</h1>
<blockquote>
<p>결재문서</p>
</blockquote>
<h2 id="파일-내-함수-정보">파일 내 함수 정보</h2>
<p><em>gvm/models/gvm_sign.py</em></p>
<ul>
<li>결재라인 동작</li>
<li>결재 로직 계산</li>
</ul>
<p><em>gvm/models/sendmail.py</em></p>
<ul>
<li>메일 발송 동작</li>
</ul>
<p><em>gvm/data/gvm_data.xml</em></p>
<ul>
<li>문서 번호 시퀀스</li>
</ul>
<h2 id="의존-관계">의존 관계</h2>
<p>project</p>
<ul>
<li>지출결의서, 출장비정산서 내역 project에 띄워주도록 되어 있음</li>
</ul>
<p>hr_employee</p>
<ul>
<li>직원정보를 기준으로 결재문서가 작성됨</li>
</ul>
<p>analytic</p>
<ul>
<li>잔업확인 시 필요</li>
</ul>
<p>gvm_mrp</p>
<ul>
<li>gvm 업데이트 시 gvm_mrp가 초기화되므로 반드시 gvm_mrp도 업데이트 해야 함</li>
</ul>
<h2 id="메뉴얼">메뉴얼</h2>

