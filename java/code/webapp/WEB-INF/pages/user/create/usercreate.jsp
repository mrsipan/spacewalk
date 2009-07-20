<%@ taglib uri="http://rhn.redhat.com/rhn" prefix="rhn" %>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<%@ taglib uri="http://jakarta.apache.org/struts/tags-html" prefix="html" %>
<%@ taglib uri="http://jakarta.apache.org/struts/tags-bean" prefix="bean" %>
<html:xhtml/>
<html>
<body>
<script language="javascript" src="/javascript/display.js"></script>


<!-- Setup the account_type variable, which is used throughout this page -->
<c:if test="${empty param.account_type}">
  <c:set var="account_type" value="create_corporate" scope="page" />
</c:if>
<c:if test="${!empty param.account_type}">
  <c:set var="account_type" value="${param.account_type}" scope="page"/>
</c:if>

<c:if test="${account_type == 'into_org'}" >
  <rhn:toolbar base="h1" img="/img/rhn-icon-users.gif" imgAlt="user.common.userAlt"
       helpUrl="/rhn/help/reference/en-US/s1-sm-users.jsp">
  <bean:message key="usercreate.toolbar" />
  </rhn:toolbar>
</c:if>


  <c:if test="${empty param.action_path}">
    <c:set var="action_path" value="/newlogin/CreateSatelliteSubmit" scope="page" />
  </c:if>
  <c:if test="${!empty param.action_path}">
    <c:set var="action_path" value="${param.action_path}" scope="page"/>
  </c:if>
<html:form action="${action_path}">
  
  <h2><bean:message key="usercreate.login" /></h2>

  <table class="details" align="center">
    <tr>
      <th><rhn:required-field key="desiredlogin"/>:</th>
      <td>
        <html:text property="login" size="15" maxlength="45"/>
      </td>
    </tr>
    <tr>
      <th><bean:message key="desiredpass" />
       <span name="password-asterisk" class="required-form-field">*</span>:</th>
      <td>
        <html:password property="desiredpassword" size="15" maxlength="32"/>
      </td>
    </tr>
    <tr>
      <th><bean:message key="confirmpass" />
      <span name="password-asterisk" class="required-form-field">*</span>:</th>
      <td>
        <html:password property="desiredpasswordConfirm" size="15" maxlength="32"/>
      </td>
    </tr>
    <c:if test="${displaypam == 'true' && account_type != 'create_sat'}">
      <tr>
        <th><bean:message key="usercreate.jsp.pam"/></th>
        <td>
          <c:choose>
            <c:when test="${displaypamcheckbox == 'true'}">
            <html:checkbox property="usepam" onclick="toggleVisibilityByName('password-asterisk')"/> 
            <bean:message key="usercreate.jsp.pam.instructions"/> <br/>
            <strong><span style="font-size: 10px">
                <bean:message key="usercreate.jsp.pam.instructions.note"/>
            </span></strong>
            </c:when>
            <c:otherwise>
              <bean:message key="usercreate.jsp.pam.reference"/>
            </c:otherwise>
          </c:choose>
        </td>
      </tr>
    </c:if>
  </table>
  
  <h2><bean:message key="usercreate.accountInfo" /></h2>
  <table class="details" align="center">
    <tr>
      <th><rhn:required-field key="usercreate.names"/>:</th>
      <td>
        <html:select property="prefix">
          <html:options collection="availablePrefixes"
            property="value"
            labelProperty="label" />
        </html:select>

        <html:text property="firstNames" size="15" maxlength="40"/>
        <html:text property="lastName" size="15" maxlength="40"/>
      </td>
    </tr>

    <tr>
       <th><rhn:required-field key="email"/>:</th>
       <td>
           <html:text property="email" size="20" />
       </td>
    </tr>
<c:if test="${account_type == 'create_corporate'}" >
    <tr>
      <th><rhn:required-field key="userdetails.jsp.company"/>:
      </th>
      <td>
        <html:text property="company" size="15" maxlength="100"/>
      </td>
    </tr>

    <tr>
      <th><bean:message key="userdetails.jsp.position" />:</th>
      <td>
        <html:text property="title" size="15" maxlength="100"/>
      </td>
    </tr>
</c:if>
<html:hidden property="account_type" value="${account_type}" />

    <tr>
      <td style="border: 0; text-align: center" colspan="2"><span class="required-form-field">*</span> - <bean:message key="usercreate.requiredField" /></td>
    </tr>
</table>



<div align="right">
<html:submit>
  <bean:message key="usercreate.jsp.createlogin"/>
</html:submit>
</div>


</html:form>

<%-- This makes sure that the asterisks toggle correctly. Before, they could get off 
     if the user checked the usepam checkbox, submitted the form, and had errors. Then
     the form would start with the box checked but the asterisks visible.
--%>
<script language="javascript">
  var items = document.getElementsByName('password-asterisk');
  if (document.userCreateForm.usepam.checked == true) {
    for (var i = 0; i < items.length; i++) {
      items[i].style.display = "none";
    }
  }
  else {
    for (var i = 0; i < items.length; i++) {
      items[i].style.display = "";
    }
  }
</script>
</body>
</html>
