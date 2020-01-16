---


---

<blockquote>
<p>Written with <a href="https://stackedit.io/">StackEdit</a>.</p>
</blockquote>
<h1 id="odoocopy">odoocopy</h1>
<p>Copy Odoo (<a href="https://github.com/odoo/odoo.git">https://github.com/odoo/odoo.git</a>)<br>
document - <a href="https://www.odoo.com/documentation/10.0/">https://www.odoo.com/documentation/10.0/</a></p>
<h2 id="파일-관리-방법">파일 관리 방법</h2>
<p>test 시 test-server 에서 진행 후 본서버로 update<br>
temp 에서 master로 push</p>
<ol>
<li>(테스트서버) <code>git commit -a -m "업데이트 정보 간단히 입력"</code></li>
<li>(테스트서버) <code>git push origin temp</code></li>
</ol>
<ul>
<li>push 안될 경우</li>
</ul>
<pre><code>  git pull origin temp
     - 서버에 있는 파일을 다시 받아온다.
     - 받아왔을 때 Conflict 있으면 없애줘야 한다.
     - 수정 후 git commit부터 다시 해야 함

	 - aborting 뜰 경우
	 - 목록에 있는 파일 삭제 후
	 - git pull origin temp

	 - 진행 후 다시 commit 부터
	 - git commit -a -m "업데이트 정보"
	 - git push origin temp
</code></pre>
<ol start="3">
<li>github.com에서 pull request</li>
</ol>
<pre><code>   - pull request
   - merge
   - merge confirm
</code></pre>
<ol start="4">
<li>(본서버) <code>git pull</code></li>
</ol>
<ul>
<li>본서버에서 수정한 것이 남아있으면 겹침</li>
</ul>
<pre><code>   - git stash
   - git pull
   - git stash pop
   - conflict 수정
</code></pre>
<ul>
<li>수정 후 master 다시 업데이트해서 파일 같게 해주기</li>
</ul>
<pre><code>     - git commit -a -m ""
     - git push
</code></pre>
<h2 id="업로드-필요한-파일">업로드 필요한 파일</h2>
<p>project_issue</p>
<ol>
<li>.gitignore 에 있는 폴더명 삭제</li>
<li>git add 폴더명</li>
<li>git commit -a -m “”</li>
<li>git push origin temp</li>
</ol>
<h2 id="이메일-설정">이메일 설정</h2>
<p>mailplug - 설정 - 메일 설정 - POP3/IMAP 설정 - 사용함으로 변경<br>
config.ini 파일에서 메일 지정 해줘야 함</p>
<h2 id="설정">설정</h2>
<p>일반설정 &gt; 인쇄파일설정(전체 템플릿)<br>
번역 &gt; 언어 &gt; 날짜형식 변경 가능<br>
번역 &gt; Translated Terms &gt; 개별적으로 단어 번역 가능<br>
기술 &gt; 하위유형 &gt; 토론,노트 기본되있는지 확인 (Discuss에 표시 안 될 경우)<br>
기술 &gt; 서식 &gt; 인쇄파일형식 설정 할 수 있음(개별 템플릿)</p>
<p><mark>작성필요</mark></p>
<h2 id="업데이트-방법">업데이트 방법</h2>
<p>터미널에서 <code>ou 업데이트할 앱 입력</code> (ex. ou purchase)<br>
브라우저에서 메뉴 &gt; 앱 &gt; 업데이트 할 앱 찾기 &gt; Upgrade 버튼 클릭</p>
<h2 id="유용한-내장-함수">유용한 내장 함수</h2>
<p>python<br>
참조 - <a href="https://www.odoo.com/documentation/10.0/reference/orm.html">https://www.odoo.com/documentation/10.0/reference/orm.html</a></p>
<ul>
<li>create, write, unlink, search</li>
<li>@api.onchange(‘필드명’)
<ul>
<li>함수 위에 적으면 필드명에 적은 필드 변경 시 함수 실행</li>
</ul>
</li>
<li>@api.depends(‘필드명’)
<ul>
<li>compute 함수 사용 시 필드 내용 변경이 불가한데 depends에 적은 필드가 변경되면 다시 함수가 실행된다.</li>
</ul>
</li>
</ul>
<p>javascript<br>
참조 - <a href="https://www.odoo.com/documentation/10.0/reference/javascript.html">https://www.odoo.com/documentation/10.0/reference/javascript.html</a></p>
<ul>
<li>query</li>
</ul>
<h2 id="문제-발생-시-해결법-찾는-팁">문제 발생 시 해결법 찾는 팁</h2>
<h2 id="앱-추가하는-방법">앱 추가하는 방법</h2>
<p>외부앱 다운 시</p>
<ol>
<li><code>curl -o 파일명 주소(링크복사)</code></li>
<li><code>unzip 파일명</code></li>
<li><code>docker restart docker_web_1</code></li>
<li>Update Apps List - 갱신</li>
</ol>
<p>새로 생성 시</p>
<ol>
<li>폴더 생성</li>
<li><code>__init__.py,__manifest__.py, models, views</code>를 다른곳에서 복사</li>
<li><code>__init__.py</code></li>
<li><code>__manifest__.py</code>
<ul>
<li><code>이름, 의존앱, 뷰파일 입력</code></li>
<li>depends(의존앱)가 없으면 꼭 지워야 함</li>
</ul>
</li>
<li>models
<ul>
<li><code>__init__.py</code>
<ul>
<li>python 파일 이름 입력</li>
</ul>
</li>
<li>가져온 파일 이름을 init에 적은 이름으로 변경</li>
<li>이름 변경한 파일 수정</li>
</ul>
</li>
<li>views
<ul>
<li>가져온 파일 수정</li>
</ul>
</li>
<li><code>__manifest__.py</code> 에서 views에 입력한 파일 이름 입력</li>
<li>재부팅 후 업데이트</li>
<li>앱 메뉴에서 Update Apps List 클릭 후 갱신</li>
<li>생성한 폴더명으로 검색해서 설치</li>
</ol>
<h2 id="상속-하는-법">상속 하는 법</h2>
<p>참조 - <a href="https://www.odoo.com/documentation/10.0/reference/views.html">https://www.odoo.com/documentation/10.0/reference/views.html</a><br>
xpath</p>
<ol>
<li>상속할 모델 생성</li>
</ol>
<ul>
<li>상속 모델 생성은 _inherit = ‘&lt;모델명&gt;’  으로 클래스 생성</li>
</ul>
<pre class=" language-python"><code class="prism  language-python"><span class="token keyword">class</span> <span class="token class-name">ProjectProjectInherit</span><span class="token punctuation">(</span>models<span class="token punctuation">.</span>Model<span class="token punctuation">)</span><span class="token punctuation">:</span>
    _inherit <span class="token operator">=</span> <span class="token string">'project.project'</span>
   <span class="token punctuation">.</span><span class="token punctuation">.</span><span class="token punctuation">.</span>
   <span class="token operator">&lt;</span>상속할 필드명 입력<span class="token operator">&gt;</span>
</code></pre>
<ul>
<li>상속할 모델파일 새로 생성 시 <code>&lt;app&gt;/models</code> 폴더에 <code>__init__.py</code> 에 파일 입력해줘야 함</li>
</ul>
<ol start="3">
<li>상속할 페이지 아이디 확인</li>
<li>상속할 콘텐츠 뷰 파일 접속</li>
</ol>
<ul>
<li>상속할 페이지 앱명으로 새로 파일 만들어도 되고, 기존의 파일에다가 적어도 된다</li>
</ul>
<ol start="5">
<li>상속할 페이지 아이디 넣어서 inherit 뷰 생성</li>
</ol>
<ul>
<li><code>&lt;xpath&gt;</code> 안에 상속할 페이지의 원하는 위치를 입력해준다</li>
</ul>
<pre><code>&lt;xpath expr="page[@name='manager']" position="inherit"&gt;
	&lt;field name="product"/&gt;
&lt;/xpath&gt;
</code></pre>
<h2 id="의존관계">의존관계</h2>
<p><img src="https://imgur.com/a/CcEH5ju" alt="의존관계사진"></p>
<h2 id="그-외-사용하는-모델">그 외 사용하는 모델</h2>
<p>ir_attachment</p>
<ul>
<li>첨부파일</li>
</ul>
<p>mail</p>
<ul>
<li>메일 및 코멘트 부분</li>
</ul>

