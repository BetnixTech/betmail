let currentUser=null;
let emailsCache=[], currentFolder="Inbox";

function showSignup(){ document.getElementById("loginPage").style.display="none"; document.getElementById("signupPage").style.display="block";}
function showLogin(){ document.getElementById("signupPage").style.display="none"; document.getElementById("loginPage").style.display="block";}
function showCompose(){ document.getElementById("composePage").style.display="block";}
function hideCompose(){ document.getElementById("composePage").style.display="none";}

async function signup(){
  let name=document.getElementById("signupName").value;
  let email=document.getElementById("signupEmail").value;
  let password=document.getElementById("signupPassword").value;
  let res=await fetch("/signup",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name,email,password})});
  let data=await res.json();
  if(data.status=="ok"){ alert("Signup successful"); showLogin(); }
  else document.getElementById("signupMsg").innerText=data.message;
}

async function login(){
  let email=document.getElementById("loginEmail").value;
  let password=document.getElementById("loginPassword").value;
  let res=await fetch("/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email,password})});
  let data=await res.json();
  if(data.status=="ok"){
    currentUser=email;
    document.getElementById("loginPage").style.display="none";
    document.getElementById("mailApp").style.display="block";
    document.getElementById("userInfo").innerText="Logged in as: "+data.name;
    loadFolder("Inbox");
  }else document.getElementById("loginMsg").innerText=data.message;
}

function logout(){ currentUser=null; document.getElementById("mailApp").style.display="none"; document.getElementById("loginPage").style.display="block"; }

async function fetchEmails(){
  let res=await fetch(`/emails/${currentUser}`);
  emailsCache=await res.json();
}

async function loadFolder(folder){
  currentFolder=folder;
  await fetchEmails();
  let filtered=[];
  if(folder=="Inbox") filtered=emailsCache.filter(e=>e.to===currentUser);
  else if(folder=="Sent") filtered=emailsCache.filter(e=>e.from===currentUser);
  else if(folder=="Drafts") filtered=emailsCache.filter(e=>e.from===currentUser && e.draft);
  else if(folder=="Trash") filtered=emailsCache.filter(e=>e.trash);
  renderEmails(filtered);
}

function renderEmails(emails){
  let list=document.getElementById("emailList");
  list.innerHTML="";
  emails.forEach(e=>{
    let div=document.createElement("div");
    div.className="emailItem";
    div.innerHTML=`<strong>${e.subject}</strong> From: ${e.from} To: ${e.to} <span class="timestamp">${e.timestamp}</span>
    <button onclick="deleteEmail(${e.id})">Delete</button><p>${e.body}</p>`;
    list.appendChild(div);
  });
}

async function sendEmail(){
  let to=document.getElementById("to").value;
  let subject=document.getElementById("subject").value;
  let body=document.getElementById("body").value;
  await fetch("/send",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({from:currentUser,to,subject,body,draft:false})});
  hideCompose(); loadFolder("Inbox");
}

async function saveDraft(){
  let to=document.getElementById("to").value;
  let subject=document.getElementById("subject").value;
  let body=document.getElementById("body").value;
  await fetch("/send",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({from:currentUser,to,subject,body,draft:true})});
  hideCompose(); loadFolder("Drafts");
}

async function deleteEmail(id){
  await fetch("/delete",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({id})});
  loadFolder(currentFolder);
}

function searchEmails(){
  let query=document.getElementById("searchBox").value.toLowerCase();
  let filtered=emailsCache.filter(e=>
    e.subject.toLowerCase().includes(query)||
    e.from.toLowerCase().includes(query)||
    e.to.toLowerCase().includes(query)||
    e.body.toLowerCase().includes(query)
  );
  renderEmails(filtered);
}
