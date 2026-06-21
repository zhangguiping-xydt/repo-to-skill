using System;

public class BillApplyModel
{
    public string EmployeeInfo { get; set; }
    public DateTime ApplyStartDateTime { get; set; }
    public DateTime ApplyEndDateTime { get; set; }
    public bool IsContainHoliday { get; set; }
    public int BillType { get; set; }
}

public class BillApplyTimeLenth
{
    public decimal TimeLenthUintDay { get; set; }
    public decimal TimeLenthUintHour { get; set; }
}

public class KQWorkDateBL
{
    public BillApplyTimeLenth CalculateTimeLength(BillApplyModel model)
    {
        return new BillApplyTimeLenth();
    }
}
