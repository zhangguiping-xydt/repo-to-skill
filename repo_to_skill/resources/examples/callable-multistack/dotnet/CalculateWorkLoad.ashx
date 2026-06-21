<%@ WebHandler Language="C#" Class="CalculateWorkLoad" %>
using System;
using System.Web;
using System.IO;
using Newtonsoft.Json;

public class CalculateWorkLoad : IHttpHandler
{
    public void ProcessRequest(HttpContext context)
    {
        string body = new StreamReader(context.Request.InputStream).ReadToEnd();
        BillApplyModel model = JsonConvert.DeserializeObject<BillApplyModel>(body);
        BillApplyTimeLenth result = KQWorkDateBL.CalculateTimeLength(model);
        context.Response.Write(JsonConvert.SerializeObject(result));
    }

    public bool IsReusable { get { return false; } }
}
