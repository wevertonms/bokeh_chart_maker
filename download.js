/*global source*/
/*eslint no-undef: "error"*/
const fileName = source.data["file_name"][0];
const fileText = source.data["html"][0].toString();
const blob = new Blob([fileText], { type: "text/csv;charset=utf-8;" });

//addresses IE
if (navigator.msSaveBlob) {
  navigator.msSaveBlob(blob, fileName);
} else {
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = fileName;
  link.target = "_blank";
  link.style.visibility = "hidden";
  link.dispatchEvent(new MouseEvent("click"));
}
